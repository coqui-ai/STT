#ifndef COQUI_STT_H
#define COQUI_STT_H

#ifdef __cplusplus
extern "C" {
#endif

#ifndef SWIG
    #if defined _MSC_VER
        #define STT_EXPORT __declspec(dllexport)
    #else
        #define STT_EXPORT __attribute__ ((visibility("default")))
    #endif /*End of _MSC_VER*/
#else
    #define STT_EXPORT
#endif

// For the decoder package we include this header but should only expose
// the error info, so guard all the other definitions out.
#ifndef SWIG_ERRORS_ONLY

typedef struct ModelState ModelState;

typedef struct StreamingState StreamingState;

/**
 * @brief Stores text of an individual token, along with its timing information
 */
typedef struct TokenMetadata {
  /** The text corresponding to this token */
  const char* const text;

  /** Position of the token in units of 20ms */
  const unsigned int timestep;

  /** Position of the token in seconds */
  const float start_time;
} TokenMetadata;

/**
 * @brief A single transcript computed by the model, including a confidence
 *        value and the metadata for its constituent tokens.
 */
typedef struct CandidateTranscript {
  /** Array of TokenMetadata objects */
  const TokenMetadata* const tokens;
  /** Size of the tokens array */
  const unsigned int num_tokens;
  /** Approximated confidence value for this transcript. This is roughly the
   * sum of the acoustic model logit values for each timestep/character that
   * contributed to the creation of this transcript.
   */
  const double confidence;
} CandidateTranscript;

/**
 * @brief An array of CandidateTranscript objects computed by the model.
 */
typedef struct Metadata {
  /** Array of CandidateTranscript objects */
  const CandidateTranscript* const transcripts;
  /** Size of the transcripts array */
  const unsigned int num_transcripts;
} Metadata;

#endif /* SWIG_ERRORS_ONLY */

// sphinx-doc: error_code_listing_start

#define STT_FOR_EACH_ERROR(APPLY) \
  APPLY(STT_ERR_OK,                      0x0000, "No error.") \
  APPLY(STT_ERR_NO_MODEL,                0x1000, "Missing model information.") \
  APPLY(STT_ERR_INVALID_ALPHABET,        0x2000, "Invalid alphabet embedded in model. (Data corruption?)") \
  APPLY(STT_ERR_INVALID_SHAPE,           0x2001, "Invalid model shape.") \
  APPLY(STT_ERR_INVALID_SCORER,          0x2002, "Invalid scorer file.") \
  APPLY(STT_ERR_MODEL_INCOMPATIBLE,      0x2003, "Incompatible model.") \
  APPLY(STT_ERR_SCORER_NOT_ENABLED,      0x2004, "External scorer is not enabled.") \
  APPLY(STT_ERR_SCORER_UNREADABLE,       0x2005, "Could not read scorer file.") \
  APPLY(STT_ERR_SCORER_INVALID_LM,       0x2006, "Could not recognize language model header in scorer.") \
  APPLY(STT_ERR_SCORER_NO_TRIE,          0x2007, "Reached end of scorer file before loading vocabulary trie.") \
  APPLY(STT_ERR_SCORER_INVALID_TRIE,     0x2008, "Invalid magic in trie header.") \
  APPLY(STT_ERR_SCORER_VERSION_MISMATCH, 0x2009, "Scorer file version does not match expected version.") \
  APPLY(STT_ERR_FAIL_INIT_MMAP,          0x3000, "Failed to initialize memory mapped model.") \
  APPLY(STT_ERR_FAIL_INIT_SESS,          0x3001, "Failed to initialize the session.") \
  APPLY(STT_ERR_FAIL_INTERPRETER,        0x3002, "Interpreter failed.") \
  APPLY(STT_ERR_FAIL_RUN_SESS,           0x3003, "Failed to run the session.") \
  APPLY(STT_ERR_FAIL_CREATE_STREAM,      0x3004, "Error creating the stream.") \
  APPLY(STT_ERR_FAIL_READ_PROTOBUF,      0x3005, "Error reading the proto buffer model file.") \
  APPLY(STT_ERR_FAIL_CREATE_SESS,        0x3006, "Failed to create session.") \
  APPLY(STT_ERR_FAIL_CREATE_MODEL,       0x3007, "Could not allocate model state.") \
  APPLY(STT_ERR_FAIL_INSERT_HOTWORD,     0x3008, "Could not insert hot-word.") \
  APPLY(STT_ERR_FAIL_CLEAR_HOTWORD,      0x3009, "Could not clear hot-words.") \
  APPLY(STT_ERR_FAIL_ERASE_HOTWORD,      0x3010, "Could not erase hot-word.")

// sphinx-doc: error_code_listing_end

enum STT_Error_Codes
{
#define DEFINE(NAME, VALUE, DESC) NAME = VALUE,
STT_FOR_EACH_ERROR(DEFINE)
#undef DEFINE
};

#ifndef SWIG_ERRORS_ONLY

/**
 * @brief An object providing an interface to a trained Coqui STT model.
 *
 * @param aModelPath The path to the frozen model graph.
 * @param[out] retval a ModelState pointer
 *
 * @return Zero on success, non-zero on failure.
 */
STT_EXPORT
int STT_CreateModel(const char* aModelPath,
                    ModelState** retval);

/**
 * @brief Get beam width value used by the model. If {@link STT_SetModelBeamWidth}
 *        was not called before, will return the default value loaded from the
 *        model file.
 *
 * @param aCtx A ModelState pointer created with {@link STT_CreateModel}.
 *
 * @return Beam width value used by the model.
 */
STT_EXPORT
unsigned int STT_GetModelBeamWidth(const ModelState* aCtx);

/**
 * @brief Set beam width value used by the model.
 *
 * @param aCtx A ModelState pointer created with {@link STT_CreateModel}.
 * @param aBeamWidth The beam width used by the model. A larger beam width value
 *                   generates better results at the cost of decoding time.
 *
 * @return Zero on success, non-zero on failure.
 */
STT_EXPORT
int STT_SetModelBeamWidth(ModelState* aCtx,
                          unsigned int aBeamWidth);

/**
 * @brief Return the sample rate expected by a model.
 *
 * @param aCtx A ModelState pointer created with {@link STT_CreateModel}.
 *
 * @return Sample rate expected by the model for its input.
 */
STT_EXPORT
int STT_GetModelSampleRate(const ModelState* aCtx);

/**
 * @brief Frees associated resources and destroys model object.
 */
STT_EXPORT
void STT_FreeModel(ModelState* ctx);

/**
 * @brief Enable decoding using an external scorer.
 *
 * @param aCtx The ModelState pointer for the model being changed.
 * @param aScorerPath The path to the external scorer file.
 *
 * @return Zero on success, non-zero on failure (invalid arguments).
 */
STT_EXPORT
int STT_EnableExternalScorer(ModelState* aCtx,
                             const char* aScorerPath);

/**
 * @brief Add a hot-word and its boost.
 *
 * Words that don't occur in the scorer (e.g. proper nouns) or strings that contain spaces won't be taken into account.
 *
 * @param aCtx The ModelState pointer for the model being changed.
 * @param word The hot-word.
 * @param boost The boost. Positive value increases and negative reduces chance of a word occuring in a transcription. Excessive positive boost might lead to splitting up of letters of the word following the hot-word.
 *
 * @return Zero on success, non-zero on failure (invalid arguments).
 */
STT_EXPORT
int STT_AddHotWord(ModelState* aCtx,
                   const char* word,
                   float boost);

/**
 * @brief Remove entry for a hot-word from the hot-words map.
 *
 * @param aCtx The ModelState pointer for the model being changed.
 * @param word The hot-word.
 *
 * @return Zero on success, non-zero on failure (invalid arguments).
 */
STT_EXPORT
int STT_EraseHotWord(ModelState* aCtx,
                     const char* word);

/**
 * @brief Removes all elements from the hot-words map.
 *
 * @param aCtx The ModelState pointer for the model being changed.
 *
 * @return Zero on success, non-zero on failure (invalid arguments).
 */
STT_EXPORT
int STT_ClearHotWords(ModelState* aCtx);

/**
 * @brief Disable decoding using an external scorer.
 *
 * @param aCtx The ModelState pointer for the model being changed.
 *
 * @return Zero on success, non-zero on failure.
 */
STT_EXPORT
int STT_DisableExternalScorer(ModelState* aCtx);

/**
 * @brief Set hyperparameters alpha and beta of the external scorer.
 *
 * @param aCtx The ModelState pointer for the model being changed.
 * @param aAlpha The alpha hyperparameter of the decoder. Language model weight.
 * @param aLMBeta The beta hyperparameter of the decoder. Word insertion weight.
 *
 * @return Zero on success, non-zero on failure.
 */
STT_EXPORT
int STT_SetScorerAlphaBeta(ModelState* aCtx,
                           float aAlpha,
                           float aBeta);

/**
 * @brief Use the Coqui STT model to convert speech to text.
 *
 * @param aCtx The ModelState pointer for the model to use.
 * @param aBuffer A 16-bit, mono raw audio signal at the appropriate
 *                sample rate (matching what the model was trained on).
 * @param aBufferSize The number of samples in the audio signal.
 *
 * @return The STT result. The user is responsible for freeing the string using
 *         {@link STT_FreeString()}. Returns NULL on error.
 */
STT_EXPORT
char* STT_SpeechToText(ModelState* aCtx,
                       const short* aBuffer,
                       unsigned int aBufferSize);

/**
 * @brief Use the Coqui STT model to convert speech to text and output results
 * including metadata.
 *
 * @param aCtx The ModelState pointer for the model to use.
 * @param aBuffer A 16-bit, mono raw audio signal at the appropriate
 *                sample rate (matching what the model was trained on).
 * @param aBufferSize The number of samples in the audio signal.
 * @param aNumResults The maximum number of CandidateTranscript structs to return. Returned value might be smaller than this.
 *
 * @return Metadata struct containing multiple CandidateTranscript structs. Each
 *         transcript has per-token metadata including timing information. The
 *         user is responsible for freeing Metadata by calling {@link STT_FreeMetadata()}.
 *         Returns NULL on error.
 */
STT_EXPORT
Metadata* STT_SpeechToTextWithMetadata(ModelState* aCtx,
                                       const short* aBuffer,
                                       unsigned int aBufferSize,
                                       unsigned int aNumResults);

/**
 * @brief Create a new streaming inference state. The streaming state returned
 *        by this function can then be passed to {@link STT_FeedAudioContent()}
 *        and {@link STT_FinishStream()}.
 *
 * @param aCtx The ModelState pointer for the model to use.
 * @param[out] retval an opaque pointer that represents the streaming state. Can
 *                    be NULL if an error occurs.
 *
 * @return Zero for success, non-zero on failure.
 */
STT_EXPORT
int STT_CreateStream(ModelState* aCtx,
                    StreamingState** retval);

/**
 * @brief Feed audio samples to an ongoing streaming inference.
 *
 * @param aSctx A streaming state pointer returned by {@link STT_CreateStream()}.
 * @param aBuffer An array of 16-bit, mono raw audio samples at the
 *                appropriate sample rate (matching what the model was trained on).
 * @param aBufferSize The number of samples in @p aBuffer.
 */
STT_EXPORT
void STT_FeedAudioContent(StreamingState* aSctx,
                          const short* aBuffer,
                          unsigned int aBufferSize);

/**
 * @brief Compute the intermediate decoding of an ongoing streaming inference.
 *
 * @param aSctx A streaming state pointer returned by {@link STT_CreateStream()}.
 *
 * @return The STT intermediate result. The user is responsible for freeing the
 *         string using {@link STT_FreeString()}.
 */
STT_EXPORT
char* STT_IntermediateDecode(const StreamingState* aSctx);

/**
 * @brief Compute the intermediate decoding of an ongoing streaming inference,
 *        return results including metadata.
 *
 * @param aSctx A streaming state pointer returned by {@link STT_CreateStream()}.
 * @param aNumResults The number of candidate transcripts to return.
 *
 * @return Metadata struct containing multiple candidate transcripts. Each transcript
 *         has per-token metadata including timing information. The user is
 *         responsible for freeing Metadata by calling {@link STT_FreeMetadata()}.
 *         Returns NULL on error.
 */
STT_EXPORT
Metadata* STT_IntermediateDecodeWithMetadata(const StreamingState* aSctx,
                                             unsigned int aNumResults);

/**
 * @brief Compute the final decoding of an ongoing streaming inference and return
 *        the result. Signals the end of an ongoing streaming inference.
 *
 * @param aSctx A streaming state pointer returned by {@link STT_CreateStream()}.
 *
 * @return The STT result. The user is responsible for freeing the string using
 *         {@link STT_FreeString()}.
 *
 * @note This method will free the state pointer (@p aSctx).
 */
STT_EXPORT
char* STT_FinishStream(StreamingState* aSctx);

/**
 * @brief Compute the final decoding of an ongoing streaming inference and return
 *        results including metadata. Signals the end of an ongoing streaming
 *        inference.
 *
 * @param aSctx A streaming state pointer returned by {@link STT_CreateStream()}.
 * @param aNumResults The number of candidate transcripts to return.
 *
 * @return Metadata struct containing multiple candidate transcripts. Each transcript
 *         has per-token metadata including timing information. The user is
 *         responsible for freeing Metadata by calling {@link STT_FreeMetadata()}.
 *         Returns NULL on error.
 *
 * @note This method will free the state pointer (@p aSctx).
 */
STT_EXPORT
Metadata* STT_FinishStreamWithMetadata(StreamingState* aSctx,
                                       unsigned int aNumResults);

/**
 * @brief Destroy a streaming state without decoding the computed logits. This
 *        can be used if you no longer need the result of an ongoing streaming
 *        inference and don't want to perform a costly decode operation.
 *
 * @param aSctx A streaming state pointer returned by {@link STT_CreateStream()}.
 *
 * @note This method will free the state pointer (@p aSctx).
 */
STT_EXPORT
void STT_FreeStream(StreamingState* aSctx);

/**
 * @brief Free memory allocated for metadata information.
 */
STT_EXPORT
void STT_FreeMetadata(Metadata* m);

/**
 * @brief Free a char* string returned by the Coqui STT API.
 */
STT_EXPORT
void STT_FreeString(char* str);

/**
 * @brief Returns the version of this library. The returned version is a semantic
 *        version (SemVer 2.0.0). The string returned must be freed with {@link STT_FreeString()}.
 *
 * @return The version string.
 */
STT_EXPORT
char* STT_Version();

/**
 * @brief Returns a textual description corresponding to an error code.
 *        The string returned must be freed with @{link STT_FreeString()}.
 *
 * @return The error description.
 */
STT_EXPORT
char* STT_ErrorCodeToErrorMessage(int aErrorCode);

#endif /* SWIG_ERRORS_ONLY */
#undef STT_EXPORT

#ifdef __cplusplus
}
#endif

#endif /* COQUI_STT_H */
