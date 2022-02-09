#ifndef CTC_BEAM_SEARCH_DECODER_H_
#define CTC_BEAM_SEARCH_DECODER_H_

#include <memory>
#include <string>
#include <vector>

#include "scorer.h"
#include "output.h"
#include "alphabet.h"

#include "flashlight/lib/text/decoder/Decoder.h"

class DecoderState
{
  int abs_time_step_;
  int space_id_;
  int blank_id_;
  size_t beam_size_;
  double cutoff_prob_;
  size_t cutoff_top_n_;
  bool start_expanding_;

  std::shared_ptr<Scorer> ext_scorer_;
  std::vector<PathTrie*> prefixes_;
  std::unique_ptr<PathTrie> prefix_root_;
  TimestepTreeNode timestep_tree_root_{nullptr, 0};
  std::unordered_map<std::string, float> hot_words_;

public:
  DecoderState() = default;
  ~DecoderState() = default;

  // Disallow copying
  DecoderState(const DecoderState&) = delete;
  DecoderState& operator=(DecoderState&) = delete;

  /* Initialize CTC beam search decoder
   *
   * Parameters:
   *     alphabet: The alphabet.
   *     beam_size: The width of beam search.
   *     cutoff_prob: Cutoff probability for pruning.
   *     cutoff_top_n: Cutoff number for pruning.
   *     ext_scorer: External scorer to evaluate a prefix, which consists of
   *                 n-gram language model scoring and word insertion term.
   *                 Default null, decoding the input sample without scorer.
   * Return:
   *     Zero on success, non-zero on failure.
  */
  int init(const Alphabet& alphabet,
           size_t beam_size,
           double cutoff_prob,
           size_t cutoff_top_n,
           std::shared_ptr<Scorer> ext_scorer,
           std::unordered_map<std::string, float> hot_words);

  /* Send data to the decoder
   *
   * Parameters:
   *     probs: 2-D vector where each element is a vector of probabilities
   *               over alphabet of one time step.
   *     time_dim: Number of timesteps.
   *     class_dim: Number of classes (alphabet length + 1 for space character).
  */
  void next(const double *probs,
            int time_dim,
            int class_dim);

  /* Get up to num_results transcriptions from current decoder state.
   *
   * Parameters:
   *     num_results: Number of beams to return.
   *
   * Return:
   *     A vector where each element is a pair of score and decoding result,
   *     in descending order.
  */
  std::vector<Output> decode(size_t num_results=1) const;
};

class FlashlightDecoderState
{
public:
  FlashlightDecoderState() = default;
  ~FlashlightDecoderState() = default;

  // Disallow copying
  FlashlightDecoderState(const FlashlightDecoderState&) = delete;
  FlashlightDecoderState& operator=(FlashlightDecoderState&) = delete;

  enum LMTokenType {
     Single     // LM units == AM units (character/byte LM)
    ,Aggregate  // LM units != AM units (word LM)
  };

  enum DecoderType {
     LexiconBased
    ,LexiconFree
  };

  enum CriterionType {
     ASG = 0
    ,CTC = 1
    ,S2S = 2
  };

  /* Initialize beam search decoder
   *
   * Parameters:
   *     alphabet: The alphabet.
   *     beam_size: The width of beam search.
   *     cutoff_prob: Cutoff probability for pruning.
   *     cutoff_top_n: Cutoff number for pruning.
   *     ext_scorer: External scorer to evaluate a prefix, which consists of
   *                 n-gram language model scoring and word insertion term.
   *                 Default null, decoding the input sample without scorer.
   * Return:
   *     Zero on success, non-zero on failure.
  */
  int init(const Alphabet& alphabet,
           size_t beam_size,
           double beam_threshold,
           size_t cutoff_top_n,
           std::shared_ptr<Scorer> ext_scorer,
           FlashlightDecoderState::LMTokenType token_type,
           fl::lib::text::Dictionary lm_tokens,
           FlashlightDecoderState::DecoderType decoder_type,
           double silence_score,
           bool merge_with_log_add,
           FlashlightDecoderState::CriterionType criterion_type,
           std::vector<float> transitions);

  /* Send data to the decoder
   *
   * Parameters:
   *     probs: 2-D vector where each element is a vector of probabilities
   *               over alphabet of one time step.
   *     time_dim: Number of timesteps.
   *     class_dim: Number of classes (alphabet length + 1 for space character).
  */
  void next(const double *probs,
            int time_dim,
            int class_dim);

  /* Return current best hypothesis, optinoally pruning hypothesis space */
  FlashlightOutput intermediate(bool prune = true);

  /* Get up to num_results transcriptions from current decoder state.
   *
   * Parameters:
   *     num_results: Number of hypotheses to return.
   *
   * Return:
   *     A vector where each element is a pair of score and decoding result,
   *     in descending order.
  */
  std::vector<FlashlightOutput> decode(size_t num_results = 1);

private:
  fl::lib::text::Dictionary lm_tokens_;
  std::unique_ptr<fl::lib::text::Decoder> decoder_impl_;
};


/* CTC Beam Search Decoder
 * Parameters:
 *     probs: 2-D vector where each element is a vector of probabilities
 *            over alphabet of one time step.
 *     time_dim: Number of timesteps.
 *     class_dim: Alphabet length (plus 1 for space character).
 *     alphabet: The alphabet.
 *     beam_size: The width of beam search.
 *     cutoff_prob: Cutoff probability for pruning.
 *     cutoff_top_n: Cutoff number for pruning.
 *     ext_scorer: External scorer to evaluate a prefix, which consists of
 *                 n-gram language model scoring and word insertion term.
 *                 Default null, decoding the input sample without scorer.
 *     hot_words: A map of hot-words and their corresponding boosts
 *                The hot-word is a string and the boost is a float.
 *     num_results: Number of beams to return.
 * Return:
 *     A vector where each element is a pair of score and decoding result,
 *     in descending order.
*/

std::vector<Output> ctc_beam_search_decoder(
    const double* probs,
    int time_dim,
    int class_dim,
    const Alphabet &alphabet,
    size_t beam_size,
    double cutoff_prob,
    size_t cutoff_top_n,
    std::shared_ptr<Scorer> ext_scorer,
    std::unordered_map<std::string, float> hot_words,
    size_t num_results=1);

/* CTC Beam Search Decoder for batch data
 * Parameters:
 *     probs: 3-D vector where each element is a 2-D vector that can be used
 *                by ctc_beam_search_decoder().
 *     alphabet: The alphabet.
 *     beam_size: The width of beam search.
 *     num_processes: Number of threads for beam search.
 *     cutoff_prob: Cutoff probability for pruning.
 *     cutoff_top_n: Cutoff number for pruning.
 *     ext_scorer: External scorer to evaluate a prefix, which consists of
 *                 n-gram language model scoring and word insertion term.
 *                 Default null, decoding the input sample without scorer.
 *     hot_words: A map of hot-words and their corresponding boosts
 *                The hot-word is a string and the boost is a float.
 *     num_results: Number of beams to return.
 * Return:
 *     A 2-D vector where each element is a vector of beam search decoding
 *     result for one audio sample.
*/
std::vector<std::vector<Output>>
ctc_beam_search_decoder_batch(
    const double* probs,
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
    size_t num_results=1);

/* Flashlight Beam Search Decoder
 * Parameters:
 *     probs: 2-D vector where each element is a vector of probabilities
 *            over alphabet of one time step.
 *     time_dim: Number of timesteps.
 *     class_dim: Alphabet length (plus 1 for space character).
 *     alphabet: The alphabet.
 *     beam_size: The width of beam search.
 *     cutoff_prob: Cutoff probability for pruning.
 *     cutoff_top_n: Cutoff number for pruning.
 *     ext_scorer: External scorer to evaluate a prefix, which consists of
 *                 n-gram language model scoring and word insertion term.
 *                 Default null, decoding the input sample without scorer.
 *     hot_words: A map of hot-words and their corresponding boosts
 *                The hot-word is a string and the boost is a float.
 *     num_results: Number of beams to return.
 * Return:
 *     A vector where each element is a pair of score and decoding result,
 *     in descending order.
*/

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
    size_t num_results);

/* Flashlight Beam Search Decoder for batch data
 * Parameters:
 *     probs: 3-D vector where each element is a 2-D vector that can be used
 *                by flashlight_beam_search_decoder().
 *     alphabet: The alphabet.
 *     beam_size: The width of beam search.
 *     num_processes: Number of threads for beam search.
 *     cutoff_prob: Cutoff probability for pruning.
 *     cutoff_top_n: Cutoff number for pruning.
 *     ext_scorer: External scorer to evaluate a prefix, which consists of
 *                 n-gram language model scoring and word insertion term.
 *                 Default null, decoding the input sample without scorer.
 *     hot_words: A map of hot-words and their corresponding boosts
 *                The hot-word is a string and the boost is a float.
 *     num_results: Number of beams to return.
 * Return:
 *     A 2-D vector where each element is a vector of beam search decoding
 *     result for one audio sample.
*/
std::vector<std::vector<FlashlightOutput>>
flashlight_beam_search_decoder_batch(
    const double* probs,
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
    size_t num_results,
    size_t num_processes);

#endif  // CTC_BEAM_SEARCH_DECODER_H_
