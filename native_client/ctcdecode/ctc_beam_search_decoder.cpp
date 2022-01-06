#include "ctc_beam_search_decoder.h"

#include <algorithm>
#include <cmath>
#include <iostream>
#include <limits>
#include <unordered_map>
#include <utility>

#include "decoder_utils.h"
#include "ThreadPool.h"
#include "fst/fstlib.h"
#include "path_trie.h"

#include "flashlight/lib/text/dictionary/Dictionary.h"
#include "flashlight/lib/text/decoder/Trie.h"
#include "flashlight/lib/text/decoder/LexiconDecoder.h"
#include "flashlight/lib/text/decoder/LexiconFreeDecoder.h"

namespace flt = fl::lib::text;

int
DecoderState::init(const Alphabet& alphabet,
                   size_t beam_size,
                   double cutoff_prob,
                   size_t cutoff_top_n,
                   std::shared_ptr<Scorer> ext_scorer,
                   std::unordered_map<std::string, float> hot_words)
{
  // assign special ids
  abs_time_step_ = 0;
  space_id_ = alphabet.GetSpaceLabel();
  blank_id_ = alphabet.GetSize();

  beam_size_ = beam_size;
  cutoff_prob_ = cutoff_prob;
  cutoff_top_n_ = cutoff_top_n;
  ext_scorer_ = ext_scorer;
  hot_words_ = hot_words;
  start_expanding_ = false;

  // init prefixes' root
  PathTrie *root = new PathTrie;
  root->score = root->log_prob_b_prev = 0.0;
  prefix_root_.reset(root);
  prefix_root_->timesteps = &timestep_tree_root_;
  prefixes_.push_back(root);

  if (ext_scorer && (bool)(ext_scorer_->dictionary)) {
    // no need for std::make_shared<>() since Copy() does 'new' behind the doors
    auto dict_ptr = std::shared_ptr<PathTrie::FstType>(ext_scorer->dictionary->Copy(true));
    root->set_dictionary(dict_ptr);
    auto matcher = std::make_shared<fst::SortedMatcher<PathTrie::FstType>>(*dict_ptr, fst::MATCH_INPUT);
    root->set_matcher(matcher);
  }

  return 0;
}

void
DecoderState::next(const double *probs,
                   int time_dim,
                   int class_dim)
{
  // prefix search over time
  for (size_t rel_time_step = 0; rel_time_step < time_dim; ++rel_time_step, ++abs_time_step_) {
    auto *prob = &probs[rel_time_step*class_dim];

    // At the start of the decoding process, we delay beam expansion so that
    // timings on the first letters is not incorrect. As soon as we see a
    // timestep with blank probability lower than 0.999, we start expanding
    // beams.
    if (prob[blank_id_] < 0.999) {
      start_expanding_ = true;
    }

    // If not expanding yet, just continue to next timestep.
    if (!start_expanding_) {
      continue;
    }

    float min_cutoff = -NUM_FLT_INF;
    bool full_beam = false;
    if (ext_scorer_) {
      size_t num_prefixes = std::min(prefixes_.size(), beam_size_);
      std::partial_sort(prefixes_.begin(),
                        prefixes_.begin() + num_prefixes,
                        prefixes_.end(),
                        prefix_compare);

      min_cutoff = prefixes_[num_prefixes - 1]->score +
                   std::log(prob[blank_id_]) - std::max(0.0, ext_scorer_->beta);
      full_beam = (num_prefixes == beam_size_);
    }

    std::vector<std::pair<size_t, float>> log_prob_idx =
        get_pruned_log_probs(prob, class_dim, cutoff_prob_, cutoff_top_n_);
    // loop over class dim
    for (size_t index = 0; index < log_prob_idx.size(); index++) {
      auto c = log_prob_idx[index].first;
      auto log_prob_c = log_prob_idx[index].second;

      for (size_t i = 0; i < prefixes_.size() && i < beam_size_; ++i) {
        auto prefix = prefixes_[i];
        if (full_beam && log_prob_c + prefix->score < min_cutoff) {
          break;
        }
        if (prefix->score == -NUM_FLT_INF) {
          continue;
        }
        assert(prefix->timesteps != nullptr);

        // blank
        if (c == blank_id_) {
          // compute probability of current path
          float log_p = log_prob_c + prefix->score;

          // combine current path with previous ones with the same prefix
          // the blank label comes last, so we can compare log_prob_nb_cur with log_p
          if (prefix->log_prob_nb_cur < log_p) {
            // keep current timesteps
            prefix->previous_timesteps = nullptr;
          }
          prefix->log_prob_b_cur =
              log_sum_exp(prefix->log_prob_b_cur, log_p);
          continue;
        }

        // repeated character
        if (c == prefix->character) {
          // compute probability of current path
          float log_p = log_prob_c + prefix->log_prob_nb_prev;

          // combine current path with previous ones with the same prefix
          if (prefix->log_prob_nb_cur < log_p) {
            // keep current timesteps
            prefix->previous_timesteps = nullptr;
          }
          prefix->log_prob_nb_cur = log_sum_exp(
              prefix->log_prob_nb_cur, log_p);
        }

        // get new prefix
        auto prefix_new = prefix->get_path_trie(c, log_prob_c);

        if (prefix_new != nullptr) {
          // compute probability of current path
          float log_p = -NUM_FLT_INF;

          if (c == prefix->character &&
              prefix->log_prob_b_prev > -NUM_FLT_INF) {
            log_p = log_prob_c + prefix->log_prob_b_prev;
          } else if (c != prefix->character) {
            log_p = log_prob_c + prefix->score;
          }

          if (ext_scorer_) {
            // skip scoring the space in word based LMs
            PathTrie* prefix_to_score;
            if (ext_scorer_->is_utf8_mode()) {
              prefix_to_score = prefix_new;
            } else {
              prefix_to_score = prefix;
            }

            // language model scoring
            if (ext_scorer_->is_scoring_boundary(prefix_to_score, c)) {
              float score = 0.0;
              std::vector<std::string> ngram;
              ngram = ext_scorer_->make_ngram(prefix_to_score);

              float hot_boost = 0.0;
              if (!hot_words_.empty()) {
                std::unordered_map<std::string, float>::iterator iter;
                // increase prob of prefix for every word
                // that matches a word in the hot-words list
                for (std::string word : ngram) {
                  iter = hot_words_.find(word);
                  if ( iter != hot_words_.end() ) {
                    // increase the log_cond_prob(prefix|LM)
                    hot_boost += iter->second;
                  }
                }
              }

              bool bos = ngram.size() < ext_scorer_->get_max_order();
              score = ( ext_scorer_->get_log_cond_prob(ngram, bos) + hot_boost ) * ext_scorer_->alpha;
              log_p += score;
              log_p += ext_scorer_->beta;
            }
          }

          // combine current path with previous ones with the same prefix
          if (prefix_new->log_prob_nb_cur < log_p) {
            // record data needed to update timesteps
            // the actual update will be done if nothing better is found
            prefix_new->previous_timesteps = prefix->timesteps;
            prefix_new->new_timestep = abs_time_step_;
          }
          prefix_new->log_prob_nb_cur =
              log_sum_exp(prefix_new->log_prob_nb_cur, log_p);
        }
      }  // end of loop over prefix
    }    // end of loop over alphabet

    // update log probs
    prefixes_.clear();
    prefix_root_->iterate_to_vec(prefixes_);

    // only preserve top beam_size prefixes
    if (prefixes_.size() > beam_size_) {
      std::nth_element(prefixes_.begin(),
                       prefixes_.begin() + beam_size_,
                       prefixes_.end(),
                       prefix_compare);
      for (size_t i = beam_size_; i < prefixes_.size(); ++i) {
        prefixes_[i]->remove();
      }

      // Remove the elements from std::vector
      prefixes_.resize(beam_size_);
    }
  }  // end of loop over time
}

std::vector<Output>
DecoderState::decode(size_t num_results) const
{
  std::vector<PathTrie*> prefixes_copy = prefixes_;
  std::unordered_map<const PathTrie*, float> scores;
  for (PathTrie* prefix : prefixes_copy) {
    scores[prefix] = prefix->score;
  }

  // score the last word of each prefix that doesn't end with space
  if (ext_scorer_) {
    for (size_t i = 0; i < beam_size_ && i < prefixes_copy.size(); ++i) {
      PathTrie* prefix = prefixes_copy[i];
      PathTrie* prefix_boundary = ext_scorer_->is_utf8_mode() ? prefix : prefix->parent;
      if (prefix_boundary && !ext_scorer_->is_scoring_boundary(prefix_boundary, prefix->character)) {
        float score = 0.0;
        std::vector<std::string> ngram = ext_scorer_->make_ngram(prefix);
        bool bos = ngram.size() < ext_scorer_->get_max_order();
        score = ext_scorer_->get_log_cond_prob(ngram, bos) * ext_scorer_->alpha;
        score += ext_scorer_->beta;
        scores[prefix] += score;
      }
    }
  }

  using namespace std::placeholders;
  size_t num_returned = std::min(prefixes_copy.size(), num_results);
  std::partial_sort(prefixes_copy.begin(),
                    prefixes_copy.begin() + num_returned,
                    prefixes_copy.end(),
                    std::bind(prefix_compare_external, _1, _2, scores));

  std::vector<Output> outputs;
  outputs.reserve(num_returned);

  for (size_t i = 0; i < num_returned; ++i) {
    Output output;
    prefixes_copy[i]->get_path_vec(output.tokens);
    output.timesteps  = get_history(prefixes_copy[i]->timesteps, &timestep_tree_root_);
    assert(output.tokens.size() == output.timesteps.size());
    output.confidence = scores[prefixes_copy[i]];
    outputs.push_back(output);
  }

  return outputs;
}

int
FlashlightDecoderState::init(
  const Alphabet& alphabet,
  size_t beam_size,
  double beam_threshold,
  size_t cutoff_top_n,
  std::shared_ptr<Scorer> ext_scorer,
  FlashlightDecoderState::LMTokenType token_type,
  flt::Dictionary lm_tokens,
  FlashlightDecoderState::DecoderType decoder_type,
  double silence_score,
  bool merge_with_log_add,
  FlashlightDecoderState::CriterionType criterion_type,
  std::vector<float> transitions)
{
  // Lexicon-free decoder must use single-token based LM
  if (decoder_type == LexiconFree) {
    assert(token_type == Single);
  }

  // Build lexicon index to LM index map
  if (!lm_tokens.contains("<unk>")) {
    lm_tokens.addEntry("<unk>");
  }
  ext_scorer->load_words(lm_tokens);
  lm_tokens_ = lm_tokens;

  // Convert our criterion type to Flashlight type
  flt::CriterionType flt_criterion;
  switch (criterion_type) {
    case ASG: flt_criterion = flt::CriterionType::ASG; break;
    case CTC: flt_criterion = flt::CriterionType::CTC; break;
    case S2S: flt_criterion = flt::CriterionType::S2S; break;
    default: assert(false);
  }

  // Build Trie
  std::shared_ptr<flt::Trie> trie = nullptr;
  auto startState = ext_scorer->start(false);
  if (token_type == Aggregate || decoder_type == LexiconBased) {
    trie = std::make_shared<flt::Trie>(lm_tokens.indexSize(), alphabet.GetSpaceLabel());
    for (int i = 0; i < lm_tokens.entrySize(); ++i) {
      const std::string entry = lm_tokens.getEntry(i);
      if (entry[0] == '<') { // don't insert <s>, </s> and <unk>
        continue;
      }
      float score = -1;
      if (token_type == Aggregate) {
        flt::LMStatePtr dummyState;
        std::tie(dummyState, score) = ext_scorer->score(startState, i);
      }
      std::vector<unsigned int> encoded = alphabet.Encode(entry);
      std::vector<int> encoded_s(encoded.begin(), encoded.end());
      trie->insert(encoded_s, i, score);
    }

    // Smear trie
    trie->smear(flt::SmearingMode::MAX);
  }

  // Query unknown token score
  int unknown_word_index = lm_tokens.getIndex("<unk>");
  float unknown_score = -std::numeric_limits<float>::infinity();
  if (token_type == Aggregate) {
    std::tie(std::ignore, unknown_score) =
      ext_scorer->score(startState, unknown_word_index);
  }

  // Make sure conversions from uint to int below don't trip us
  assert(beam_size < INT_MAX);
  assert(cutoff_top_n < INT_MAX);

  if (decoder_type == LexiconBased) {
    flt::LexiconDecoderOptions opts;
    opts.beamSize = static_cast<int>(beam_size);
    opts.beamSizeToken = static_cast<int>(cutoff_top_n);
    opts.beamThreshold = beam_threshold;
    opts.lmWeight = ext_scorer->alpha;
    opts.wordScore = ext_scorer->beta;
    opts.unkScore = unknown_score;
    opts.silScore = silence_score;
    opts.logAdd = merge_with_log_add;
    opts.criterionType = flt_criterion;
    decoder_impl_.reset(new flt::LexiconDecoder(
      opts,
      trie,
      ext_scorer,
      alphabet.GetSpaceLabel(), // silence index
      alphabet.GetSize(), // blank index
      unknown_word_index,
      transitions,
      token_type == Single)
    );
  } else {
    flt::LexiconFreeDecoderOptions opts;
    opts.beamSize = static_cast<int>(beam_size);
    opts.beamSizeToken = static_cast<int>(cutoff_top_n);
    opts.beamThreshold = beam_threshold;
    opts.lmWeight = ext_scorer->alpha;
    opts.silScore = silence_score;
    opts.logAdd = merge_with_log_add;
    opts.criterionType = flt_criterion;
    decoder_impl_.reset(new flt::LexiconFreeDecoder(
      opts,
      ext_scorer,
      alphabet.GetSpaceLabel(), // silence index
      alphabet.GetSize(), // blank index
      transitions)
    );
  }

  // Init decoder for stream
  decoder_impl_->decodeBegin();

  return 0;
}

void
FlashlightDecoderState::next(
  const double *probs,
  int time_dim,
  int class_dim)
{
  std::vector<float> probs_f(probs, probs + (time_dim * class_dim) + 1);
  decoder_impl_->decodeStep(probs_f.data(), time_dim, class_dim);
}

FlashlightOutput
FlashlightDecoderState::intermediate(bool prune)
{
  flt::DecodeResult result = decoder_impl_->getBestHypothesis();
  std::vector<int> valid_words;
  for (int w : result.words) {
    if (w != -1) {
      valid_words.push_back(w);
    }
  }
  FlashlightOutput ret;
  ret.aggregate_score = result.score;
  ret.acoustic_model_score = result.amScore;
  ret.language_model_score = result.lmScore;
  ret.words = lm_tokens_.mapIndicesToEntries(valid_words); // how does this interact with token-based decoding
  ret.tokens = result.tokens;
  if (prune) {
    decoder_impl_->prune();
  }
  return ret;
}

std::vector<FlashlightOutput>
FlashlightDecoderState::decode(size_t num_results)
{
  decoder_impl_->decodeEnd();
  std::vector<flt::DecodeResult> flt_results = decoder_impl_->getAllFinalHypothesis();
  std::vector<FlashlightOutput> ret;
  for (auto result : flt_results) {
    std::vector<int> valid_words;
    for (int w : result.words) {
      if (w != -1) {
        valid_words.push_back(w);
      }
    }
    FlashlightOutput out;
    out.aggregate_score = result.score;
    out.acoustic_model_score = result.amScore;
    out.language_model_score = result.lmScore;
    out.words = lm_tokens_.mapIndicesToEntries(valid_words); // how does this interact with token-based decoding
    out.tokens = result.tokens;
    ret.push_back(out);
  }
  decoder_impl_.reset(nullptr);
  return ret;
}

std::vector<Output> ctc_beam_search_decoder(
    const double *probs,
    int time_dim,
    int class_dim,
    const Alphabet &alphabet,
    size_t beam_size,
    double cutoff_prob,
    size_t cutoff_top_n,
    std::shared_ptr<Scorer> ext_scorer,
    std::unordered_map<std::string, float> hot_words,
    size_t num_results)
{
  VALID_CHECK_EQ(alphabet.GetSize()+1, class_dim, "Number of output classes in acoustic model does not match number of labels in the alphabet file. Alphabet file must be the same one that was used to train the acoustic model.");
  DecoderState state;
  state.init(alphabet, beam_size, cutoff_prob, cutoff_top_n, ext_scorer, hot_words);
  state.next(probs, time_dim, class_dim);
  return state.decode(num_results);
}

std::vector<std::vector<Output>>
ctc_beam_search_decoder_batch(
    const double *probs,
    int batch_size,
    int time_dim,
    int class_dim,
    const int* seq_lengths,
    int seq_lengths_size,
    const Alphabet &alphabet,
    size_t beam_size,
    size_t num_processes,
    double cutoff_prob,
    size_t cutoff_top_n,
    std::shared_ptr<Scorer> ext_scorer,
    std::unordered_map<std::string, float> hot_words,
    size_t num_results)
{
  VALID_CHECK_GT(num_processes, 0, "num_processes must be nonnegative!");
  VALID_CHECK_EQ(batch_size, seq_lengths_size, "must have one sequence length per batch element");
  // thread pool
  ThreadPool pool(num_processes);

  // enqueue the tasks of decoding
  std::vector<std::future<std::vector<Output>>> res;
  for (size_t i = 0; i < batch_size; ++i) {
    res.emplace_back(pool.enqueue(ctc_beam_search_decoder,
                                  &probs[i*time_dim*class_dim],
                                  seq_lengths[i],
                                  class_dim,
                                  alphabet,
                                  beam_size,
                                  cutoff_prob,
                                  cutoff_top_n,
                                  ext_scorer,
                                  hot_words,
                                  num_results));
  }

  // get decoding results
  std::vector<std::vector<Output>> batch_results;
  for (size_t i = 0; i < batch_size; ++i) {
    batch_results.emplace_back(res[i].get());
  }
  return batch_results;
}

std::vector<FlashlightOutput>
flashlight_beam_search_decoder(
    const double* probs,
    int time_dim,
    int class_dim,
    const Alphabet& alphabet,
    size_t beam_size,
    double beam_threshold,
    size_t cutoff_top_n,
    std::shared_ptr<Scorer> ext_scorer,
    FlashlightDecoderState::LMTokenType token_type,
    const std::vector<std::string>& lm_tokens,
    FlashlightDecoderState::DecoderType decoder_type,
    double silence_score,
    bool merge_with_log_add,
    FlashlightDecoderState::CriterionType criterion_type,
    std::vector<float> transitions,
    size_t num_results)
{
  VALID_CHECK_EQ(alphabet.GetSize()+1, class_dim, "Number of output classes in acoustic model does not match number of labels in the alphabet file. Alphabet file must be the same one that was used to train the acoustic model.");
  flt::Dictionary tokens_dict;
  for (auto str : lm_tokens) {
    tokens_dict.addEntry(str);
  }
  FlashlightDecoderState state;
  state.init(
    alphabet,
    beam_size,
    beam_threshold,
    cutoff_top_n,
    ext_scorer,
    token_type,
    tokens_dict,
    decoder_type,
    silence_score,
    merge_with_log_add,
    criterion_type,
    transitions);
  state.next(probs, time_dim, class_dim);
  return state.decode(num_results);
}

std::vector<std::vector<FlashlightOutput>>
flashlight_beam_search_decoder_batch(
    const double *probs,
    int batch_size,
    int time_dim,
    int class_dim,
    const int* seq_lengths,
    int seq_lengths_size,
    const Alphabet& alphabet,
    size_t beam_size,
    double beam_threshold,
    size_t cutoff_top_n,
    std::shared_ptr<Scorer> ext_scorer,
    FlashlightDecoderState::LMTokenType token_type,
    const std::vector<std::string>& lm_tokens,
    FlashlightDecoderState::DecoderType decoder_type,
    double silence_score,
    bool merge_with_log_add,
    FlashlightDecoderState::CriterionType criterion_type,
    std::vector<float> transitions,
    size_t num_processes,
    size_t num_results)
{
  VALID_CHECK_GT(num_processes, 0, "num_processes must be nonnegative!");
  VALID_CHECK_EQ(batch_size, seq_lengths_size, "must have one sequence length per batch element");

  ThreadPool pool(num_processes);

  // enqueue the tasks of decoding
  std::vector<std::future<std::vector<FlashlightOutput>>> res;
  for (size_t i = 0; i < batch_size; ++i) {
    res.emplace_back(pool.enqueue(flashlight_beam_search_decoder,
                                  &probs[i*time_dim*class_dim],
                                  seq_lengths[i],
                                  class_dim,
                                  alphabet,
                                  beam_size,
                                  beam_threshold,
                                  cutoff_top_n,
                                  ext_scorer,
                                  token_type,
                                  lm_tokens,
                                  decoder_type,
                                  silence_score,
                                  merge_with_log_add,
                                  criterion_type,
                                  transitions,
                                  num_results));
  }

  // get decoding results
  std::vector<std::vector<FlashlightOutput>> batch_results;
  for (size_t i = 0; i < batch_size; ++i) {
    batch_results.emplace_back(res[i].get());
  }

  return batch_results;
}
