#include <algorithm>
#ifdef _MSC_VER
  #define _USE_MATH_DEFINES
#endif
#include <cmath>
#include <iostream>
#include <memory>
#include <string>
#include <utility>
#include <vector>

#include "coqui-stt.h"
#include "alphabet.h"
#include "modelstate.h"

#include "workspace_status.h"
#include "tflitemodelstate.h"
#include "ctcdecode/ctc_beam_search_decoder.h"

#ifdef __ANDROID__
#include <android/log.h>
#define  LOG_TAG    "libstt"
#define  LOGD(...)  __android_log_print(ANDROID_LOG_DEBUG, LOG_TAG, __VA_ARGS__)
#define  LOGE(...)  __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)
#else
#define  LOGD(...)
#define  LOGE(...)
#endif // __ANDROID__

using std::vector;

/* This is the implementation of the streaming inference API.

   The streaming process uses three buffers that are fed eagerly as audio data
   is fed in. The buffers only hold the minimum amount of data needed to do a
   step in the acoustic model. The three buffers which live in StreamingState
   are:

   - audio_buffer, used to buffer audio samples until there's enough data to
     compute input features for a single window.

   - mfcc_buffer, used to buffer input features until there's enough data for
     a single timestep. Remember there's overlap in the features, each timestep
     contains n_context past feature frames, the current feature frame, and
     n_context future feature frames, for a total of 2*n_context + 1 feature
     frames per timestep.

   - batch_buffer, used to buffer timesteps until there's enough data to compute
     a batch of n_steps.

   Data flows through all three buffers as audio samples are fed via the public
   API. When audio_buffer is full, features are computed from it and pushed to
   mfcc_buffer. When mfcc_buffer is full, the timestep is copied to batch_buffer.
   When batch_buffer is full, we do a single step through the acoustic model
   and accumulate the intermediate decoding state in the DecoderState structure.

   When finishStream() is called, we return the corresponding transcript from
   the current decoder state.
*/
struct StreamingState {
  vector<float> audio_buffer_;
  vector<float> mfcc_buffer_;
  vector<float> batch_buffer_;
  vector<float> previous_state_c_;
  vector<float> previous_state_h_;
  bool keep_emissions_ = false;

  vector<double> probs_;
  ModelState* model_;
  DecoderState decoder_state_;

  StreamingState();
  ~StreamingState();

  void feedAudioContent(const short* buffer, unsigned int buffer_size);
  char* intermediateDecode() const;
  Metadata* intermediateDecodeWithMetadata(unsigned int num_results) const;
  void flushBuffers(bool addZeroMfccVectors = false);
  char* finishStream();
  Metadata* finishStreamWithMetadata(unsigned int num_results);

  void processAudioWindow(const vector<float>& buf);
  void processMfccWindow(const vector<float>& buf);
  void pushMfccBuffer(const vector<float>& buf);
  void addZeroMfccWindow();
  void processBatch(const vector<float>& buf, unsigned int n_steps);
};

StreamingState::StreamingState()
{
}

StreamingState::~StreamingState()
{
}

template<typename T>
void
shift_buffer_left(vector<T>& buf, int shift_amount)
{
  std::rotate(buf.begin(), buf.begin() + shift_amount, buf.end());
  buf.resize(buf.size() - shift_amount);
}

void
StreamingState::feedAudioContent(const short* buffer,
                                 unsigned int buffer_size)
{
  // Consume all the data that was passed in, processing full buffers if needed
  while (buffer_size > 0) {
    while (buffer_size > 0 && audio_buffer_.size() < model_->audio_win_len_) {
      // Convert i16 sample into f32
      float multiplier = 1.0f / (1 << 15);
      audio_buffer_.push_back((float)(*buffer) * multiplier);
      ++buffer;
      --buffer_size;
    }

    // If the buffer is full, process and shift it
    if (audio_buffer_.size() == model_->audio_win_len_) {
      processAudioWindow(audio_buffer_);
      // Shift data by one step
      shift_buffer_left(audio_buffer_, model_->audio_win_step_);
    }

    // Repeat until buffer empty
  }
}

char*
StreamingState::intermediateDecode() const
{
  return model_->decode(decoder_state_);
}

Metadata*
StreamingState::intermediateDecodeWithMetadata(unsigned int num_results) const
{
  Metadata *m = model_->decode_metadata(decoder_state_, num_results);

  if (keep_emissions_) {

    const size_t alphabet_size = model_->alphabet_.GetSize();
    const int num_timesteps = probs_.size() / (ModelState::BATCH_SIZE * (alphabet_size + 1));

    AcousticModelEmissions* emissions = (AcousticModelEmissions*)malloc(sizeof(AcousticModelEmissions));

    emissions->num_symbols = alphabet_size;
    emissions->num_timesteps = num_timesteps;
    emissions->symbols = (const char**)malloc(sizeof(char*)*alphabet_size + 1);
    for (int i = 0; i < alphabet_size; i++) {
        emissions->symbols[i] = strdup(model_->alphabet_.DecodeSingle(i).c_str());
    }
    emissions->symbols[alphabet_size] = strdup("\t");

    double* probs = (double*)malloc(sizeof(double)*(alphabet_size + 1)*num_timesteps);
    memcpy(probs, probs_.data(), sizeof(double)*(alphabet_size + 1)*num_timesteps);

    emissions->emissions = probs;

    Metadata* ret = (Metadata*)malloc(sizeof(Metadata));

    Metadata metadata {
      m->transcripts,  // transcripts
      m->num_transcripts, // num_transcripts
      emissions,
    };

    memcpy(ret, &metadata, sizeof(Metadata));

    return ret;
  }

  return m;
}

char*
StreamingState::finishStream()
{
  flushBuffers(true);
  return model_->decode(decoder_state_);
}

Metadata*
StreamingState::finishStreamWithMetadata(unsigned int num_results)
{
  flushBuffers(true);
  Metadata *m = model_->decode_metadata(decoder_state_, num_results);

  if (keep_emissions_) {

    const size_t alphabet_size = model_->alphabet_.GetSize();
    const int num_timesteps = probs_.size() / (ModelState::BATCH_SIZE * (alphabet_size + 1));

    AcousticModelEmissions* emissions = (AcousticModelEmissions*)malloc(sizeof(AcousticModelEmissions));

    emissions->num_symbols = alphabet_size;
    emissions->num_timesteps = num_timesteps;
    emissions->symbols = (const char**)malloc(sizeof(char*)*alphabet_size + 1);
    for (int i = 0; i < alphabet_size; i++) {
        emissions->symbols[i] = strdup(model_->alphabet_.DecodeSingle(i).c_str());
    }
    emissions->symbols[alphabet_size] = strdup("\t");

    double* probs = (double*)malloc(sizeof(double)*(alphabet_size + 1)*num_timesteps);
    memcpy(probs, probs_.data(), sizeof(double)*(alphabet_size + 1)*num_timesteps);

    emissions->emissions = probs;

    Metadata* ret = (Metadata*)malloc(sizeof(Metadata));

    Metadata metadata {
      m->transcripts,  // transcripts
      m->num_transcripts, // num_transcripts
      emissions,
    };

    memcpy(ret, &metadata, sizeof(Metadata));

    return ret;
  }

  return m;
}

void
StreamingState::processAudioWindow(const vector<float>& buf)
{
  // Compute MFCC features
  vector<float> mfcc;
  mfcc.reserve(model_->n_features_);
  model_->compute_mfcc(buf, mfcc);
  pushMfccBuffer(mfcc);
}

void
StreamingState::flushBuffers(bool addZeroMfccVectors)
{
  // Flush audio buffer
  processAudioWindow(audio_buffer_);

  if (addZeroMfccVectors) {
    // Add empty mfcc vectors at end of sample
    for (int i = 0; i < model_->n_context_; ++i) {
      addZeroMfccWindow();
    }
  }

  // Process batch if there's inputs to be processed
  if (batch_buffer_.size() > 0) {
    processBatch(batch_buffer_, batch_buffer_.size()/model_->mfcc_feats_per_timestep_);
    batch_buffer_.resize(0);
  }
}

void
StreamingState::addZeroMfccWindow()
{
  vector<float> zero_buffer(model_->n_features_, 0.f);
  pushMfccBuffer(zero_buffer);
}

template<typename InputIt, typename OutputIt>
InputIt
copy_up_to_n(InputIt from_begin, InputIt from_end, OutputIt to_begin, int max_elems)
{
  int next_copy_amount = std::min<int>(std::distance(from_begin, from_end), max_elems);
  std::copy_n(from_begin, next_copy_amount, to_begin);
  return from_begin + next_copy_amount;
}

void
StreamingState::pushMfccBuffer(const vector<float>& buf)
{
  auto start = buf.begin();
  auto end = buf.end();
  while (start != end) {
    // Copy from input buffer to mfcc_buffer, stopping if we have a full context window
    start = copy_up_to_n(start, end, std::back_inserter(mfcc_buffer_),
                         model_->mfcc_feats_per_timestep_ - mfcc_buffer_.size());
    assert(mfcc_buffer_.size() <= model_->mfcc_feats_per_timestep_);

    // If we have a full context window
    if (mfcc_buffer_.size() == model_->mfcc_feats_per_timestep_) {
      processMfccWindow(mfcc_buffer_);
      // Shift data by one step of one mfcc feature vector
      shift_buffer_left(mfcc_buffer_, model_->n_features_);
    }
  }
}

void
StreamingState::processMfccWindow(const vector<float>& buf)
{
  auto start = buf.begin();
  auto end = buf.end();
  while (start != end) {
    // Copy from input buffer to batch_buffer, stopping if we have a full batch
    start = copy_up_to_n(start, end, std::back_inserter(batch_buffer_),
                         model_->n_steps_ * model_->mfcc_feats_per_timestep_ - batch_buffer_.size());
    assert(batch_buffer_.size() <= model_->n_steps_ * model_->mfcc_feats_per_timestep_);

    // If we have a full batch
    if (batch_buffer_.size() == model_->n_steps_ * model_->mfcc_feats_per_timestep_) {
      processBatch(batch_buffer_, model_->n_steps_);
      batch_buffer_.resize(0);
    }
  }
}

void
StreamingState::processBatch(const vector<float>& buf, unsigned int n_steps)
{
  vector<float> logits;
  model_->infer(buf,
                n_steps,
                previous_state_c_,
                previous_state_h_,
                logits,
                previous_state_c_,
                previous_state_h_);

  const size_t num_classes = model_->alphabet_.GetSize() + 1; // +1 for blank
  const int n_frames = logits.size() / (ModelState::BATCH_SIZE * num_classes);

  // Convert logits to double
  vector<double> inputs(logits.begin(), logits.end());
  if (keep_emissions_) {
    probs_ = inputs;
  }
  decoder_state_.next(inputs.data(),
                      n_frames,
                      num_classes);
}

int
CreateModelImpl(const char* aModelString,
                bool init_from_bytes,
                ModelState** retval,
                unsigned int aBufferSize = 0)
{
  *retval = nullptr;

  std::cerr << "TensorFlow: " << tf_local_git_version() << std::endl;
  std::cerr << " Coqui STT: " << ds_git_version() << std::endl;
#ifdef __ANDROID__
  LOGE("TensorFlow: %s", tf_local_git_version());
  LOGD("TensorFlow: %s", tf_local_git_version());
  LOGE(" Coqui STT: %s", ds_git_version());
  LOGD(" Coqui STT: %s", ds_git_version());
#endif

  if ((!init_from_bytes && !strlen(aModelString)) || (init_from_bytes && !aBufferSize)) {
    std::cerr << "No model specified, cannot continue." << std::endl;
    return STT_ERR_NO_MODEL;
  }

  std::unique_ptr<ModelState> model(new TFLiteModelState());

  if (!model) {
    std::cerr << "Could not allocate model state." << std::endl;
    return STT_ERR_FAIL_CREATE_MODEL;
  }

  int err = model->init(aModelString, init_from_bytes, aBufferSize);
  if (err != STT_ERR_OK) {
    return err;
  }

  *retval = model.release();
  return STT_ERR_OK;
}

int
STT_CreateModel(const char* aModelPath,
                ModelState** retval)
{
  return CreateModelImpl(aModelPath, false, retval);
}

int
STT_CreateModelFromBuffer(const char* aModelBuffer,
                          unsigned int aBufferSize,
                          ModelState** retval)
{
  return CreateModelImpl(aModelBuffer, true, retval, aBufferSize);
}

unsigned int
STT_GetModelBeamWidth(const ModelState* aCtx)
{
  return aCtx->beam_width_;
}

int
STT_SetModelBeamWidth(ModelState* aCtx, unsigned int aBeamWidth)
{
  aCtx->beam_width_ = aBeamWidth;
  return 0;
}

int
STT_GetModelSampleRate(const ModelState* aCtx)
{
  return aCtx->sample_rate_;
}

void
STT_FreeModel(ModelState* ctx)
{
  delete ctx;
}

int
EnableExternalScorerImpl(ModelState* aCtx,
                         const std::string& aPathOrBuffer,
                         bool aInitFromBuffer)
{
  std::unique_ptr<Scorer> scorer(new Scorer());

  int err;
  if (aInitFromBuffer) {
    err = scorer->init_from_buffer(aPathOrBuffer, aCtx->alphabet_);
  } else {
    err = scorer->init_from_filepath(aPathOrBuffer, aCtx->alphabet_);
  }

  if (err != STT_ERR_OK) {
    return STT_ERR_INVALID_SCORER;
  }
  aCtx->scorer_ = std::move(scorer);
  return STT_ERR_OK;
}

int
STT_EnableExternalScorer(ModelState* aCtx,
                         const char* aScorerPath)
{
  return EnableExternalScorerImpl(aCtx, aScorerPath, false);
}

int
STT_EnableExternalScorerFromBuffer(ModelState* aCtx,
                                   const char* aScorerBuffer,
                                   unsigned int aBufferSize)
{
  std::string buffer(aScorerBuffer, aBufferSize);
  return EnableExternalScorerImpl(aCtx, buffer, true);
}

int
STT_AddHotWord(ModelState* aCtx,
              const char* word,
              float boost)
{
  if (aCtx->scorer_) {
    const int size_before = aCtx->hot_words_.size();
    aCtx->hot_words_.insert( std::pair<std::string,float> (word, boost) );
    const int size_after = aCtx->hot_words_.size();
    if (size_before == size_after) {
      return STT_ERR_FAIL_INSERT_HOTWORD;
    }
    return STT_ERR_OK;
  }
  return STT_ERR_SCORER_NOT_ENABLED;
}

int
STT_EraseHotWord(ModelState* aCtx,
                const char* word)
{
  if (aCtx->scorer_) {
    const int size_before = aCtx->hot_words_.size();
    int err = aCtx->hot_words_.erase(word);
    const int size_after = aCtx->hot_words_.size();
    if (size_before == size_after) {
      return STT_ERR_FAIL_ERASE_HOTWORD;
    }
    return STT_ERR_OK;
  }
  return STT_ERR_SCORER_NOT_ENABLED;
}

int
STT_ClearHotWords(ModelState* aCtx)
{
  if (aCtx->scorer_) {
    aCtx->hot_words_.clear();
    const int size_after = aCtx->hot_words_.size();
    if (size_after != 0) {
      return STT_ERR_FAIL_CLEAR_HOTWORD;
    }
    return STT_ERR_OK;
  }
  return STT_ERR_SCORER_NOT_ENABLED;
}

int
STT_DisableExternalScorer(ModelState* aCtx)
{
  if (aCtx->scorer_) {
    aCtx->scorer_.reset();
    return STT_ERR_OK;
  }
  return STT_ERR_SCORER_NOT_ENABLED;
}

int STT_SetScorerAlphaBeta(ModelState* aCtx,
                          float aAlpha,
                          float aBeta)
{
  if (aCtx->scorer_) {
    aCtx->scorer_->reset_params(aAlpha, aBeta);
    return STT_ERR_OK;
  }
  return STT_ERR_SCORER_NOT_ENABLED;
}

int
STT_CreateStream(ModelState* aCtx,
                StreamingState** retval)
{
  *retval = nullptr;

  std::unique_ptr<StreamingState> ctx(new StreamingState());
  if (!ctx) {
    std::cerr << "Could not allocate streaming state." << std::endl;
    return STT_ERR_FAIL_CREATE_STREAM;
  }

  ctx->audio_buffer_.reserve(aCtx->audio_win_len_);
  ctx->mfcc_buffer_.reserve(aCtx->mfcc_feats_per_timestep_);
  ctx->mfcc_buffer_.resize(aCtx->n_features_*aCtx->n_context_, 0.f);
  ctx->batch_buffer_.reserve(aCtx->n_steps_ * aCtx->mfcc_feats_per_timestep_);
  ctx->previous_state_c_.resize(aCtx->state_size_, 0.f);
  ctx->previous_state_h_.resize(aCtx->state_size_, 0.f);
  ctx->model_ = aCtx;

  const int cutoff_top_n = 40;
  const double cutoff_prob = 1.0;

  ctx->decoder_state_.init(aCtx->alphabet_,
                           aCtx->beam_width_,
                           cutoff_prob,
                           cutoff_top_n,
                           aCtx->scorer_,
                           aCtx->hot_words_);

  *retval = ctx.release();
  return STT_ERR_OK;
}

int
CreateStreamWithEmissions(ModelState* aCtx,
                StreamingState** retval)
{
  *retval = nullptr;

  std::unique_ptr<StreamingState> ctx(new StreamingState());
  if (!ctx) {
    std::cerr << "Could not allocate streaming state." << std::endl;
    return STT_ERR_FAIL_CREATE_STREAM;
  }

  ctx->audio_buffer_.reserve(aCtx->audio_win_len_);
  ctx->mfcc_buffer_.reserve(aCtx->mfcc_feats_per_timestep_);
  ctx->mfcc_buffer_.resize(aCtx->n_features_*aCtx->n_context_, 0.f);
  ctx->batch_buffer_.reserve(aCtx->n_steps_ * aCtx->mfcc_feats_per_timestep_);
  ctx->previous_state_c_.resize(aCtx->state_size_, 0.f);
  ctx->previous_state_h_.resize(aCtx->state_size_, 0.f);
  ctx->model_ = aCtx;
  ctx->keep_emissions_ = true;

  const int cutoff_top_n = 40;
  const double cutoff_prob = 1.0;

  ctx->decoder_state_.init(aCtx->alphabet_,
                           aCtx->beam_width_,
                           cutoff_prob,
                           cutoff_top_n,
                           aCtx->scorer_,
                           aCtx->hot_words_);

  *retval = ctx.release();
  return STT_ERR_OK;
}

void
STT_FeedAudioContent(StreamingState* aSctx,
                    const short* aBuffer,
                    unsigned int aBufferSize)
{
  aSctx->feedAudioContent(aBuffer, aBufferSize);
}

char*
STT_IntermediateDecode(const StreamingState* aSctx)
{
  return aSctx->intermediateDecode();
}

Metadata*
STT_IntermediateDecodeWithMetadata(const StreamingState* aSctx,
                                  unsigned int aNumResults)
{
  return aSctx->intermediateDecodeWithMetadata(aNumResults);
}

char*
STT_IntermediateDecodeFlushBuffers(StreamingState* aSctx)
{
  aSctx->flushBuffers();
  return aSctx->intermediateDecode();
}

Metadata*
STT_IntermediateDecodeWithMetadataFlushBuffers(StreamingState* aSctx,
                                               unsigned int aNumResults)
{
  aSctx->flushBuffers();
  return aSctx->intermediateDecodeWithMetadata(aNumResults);
}

char*
STT_FinishStream(StreamingState* aSctx)
{
  char* str = aSctx->finishStream();
  STT_FreeStream(aSctx);
  return str;
}

Metadata*
STT_FinishStreamWithMetadata(StreamingState* aSctx,
                            unsigned int aNumResults)
{
  Metadata* result = aSctx->finishStreamWithMetadata(aNumResults);
  STT_FreeStream(aSctx);
  return result;
}

StreamingState*
CreateStreamAndFeedAudioContent(ModelState* aCtx,
                                const short* aBuffer,
                                unsigned int aBufferSize)
{
  StreamingState* ctx;
  int status = STT_CreateStream(aCtx, &ctx);
  if (status != STT_ERR_OK) {
    return nullptr;
  }
  STT_FeedAudioContent(ctx, aBuffer, aBufferSize);
  return ctx;
}

char*
STT_SpeechToText(ModelState* aCtx,
                const short* aBuffer,
                unsigned int aBufferSize)
{
  StreamingState* ctx = CreateStreamAndFeedAudioContent(aCtx, aBuffer, aBufferSize);
  return STT_FinishStream(ctx);
}

Metadata*
STT_SpeechToTextWithMetadata(ModelState* aCtx,
                            const short* aBuffer,
                            unsigned int aBufferSize,
                            unsigned int aNumResults)
{
  StreamingState* ctx = CreateStreamAndFeedAudioContent(aCtx, aBuffer, aBufferSize);
  return STT_FinishStreamWithMetadata(ctx, aNumResults);
}

Metadata*
STT_SpeechToTextWithEmissions(ModelState* aCtx,
                            const short* aBuffer,
                            unsigned int aBufferSize,
                            unsigned int aNumResults)
{
  StreamingState* ctx;
  int status = CreateStreamWithEmissions(aCtx, &ctx);
  if (status != STT_ERR_OK) {
    return nullptr;
  }
  STT_FeedAudioContent(ctx, aBuffer, aBufferSize);

  return STT_FinishStreamWithMetadata(ctx, aNumResults);
}

void
STT_FreeStream(StreamingState* aSctx)
{
  delete aSctx;
}

void
STT_FreeMetadata(Metadata* m)
{
  if (m) {
    for (int i = 0; i < m->num_transcripts; ++i) {
      for (int j = 0; j < m->transcripts[i].num_tokens; ++j) {
        free((void*)m->transcripts[i].tokens[j].text);
      }

      free((void*)m->transcripts[i].tokens);
    }

    free((void*)m->transcripts);

    // Clean up logits if they are not NULL
    if (m->emissions) {

      if (m->emissions->symbols) {
        for (int i = 0; i < m->emissions->num_symbols + 1; i++) {
          free((void*)m->emissions->symbols[i]);
        }
        free((void*)m->emissions->symbols);
      }
      if (m->emissions->emissions) {
        free((void*)m->emissions->emissions);
      }
      free((void*)m->emissions);
    }
    free(m);
  }
}
void
STT_FreeString(char* str)
{
  free(str);
}

char*
STT_Version()
{
  return strdup(ds_version());
}
