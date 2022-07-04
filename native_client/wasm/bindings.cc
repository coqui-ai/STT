#include <emscripten/bind.h>

#include <iostream>
#include <string>
#include <vector>

#include "coqui-stt.h"

using namespace emscripten;

typedef struct TokenMetadataStub {
    std::string text;
    unsigned int timestep;
    float start_time;

    static TokenMetadataStub fromTokenMetadata(TokenMetadata tokenMetadata) {
        return TokenMetadataStub{
            tokenMetadata.text,
            tokenMetadata.timestep,
            tokenMetadata.start_time
        };
    }
};

typedef struct CandidateTranscriptStub {
    std::vector<TokenMetadataStub> tokens;
    double confidence;

    static CandidateTranscriptStub fromCandidateTranscript(CandidateTranscript candidateTranscript) {
        std::cout << "Converting from CandidateTranscript" << std::endl;
        std::vector<TokenMetadataStub> tokens = std::vector<TokenMetadataStub>(candidateTranscript.num_tokens);

        for (int i = 0; i < candidateTranscript.num_tokens; i++) {
            const TokenMetadata candidateToken = candidateTranscript.tokens[i];
            TokenMetadataStub token = TokenMetadataStub::fromTokenMetadata(candidateToken);
            tokens[i] = token;
        }


        return CandidateTranscriptStub{
            tokens,
            candidateTranscript.confidence
        };
    }
};

typedef struct MetadataStub {
    std::vector<CandidateTranscriptStub> transcripts;

    static MetadataStub fromMetadata(Metadata* metadata) {
        std::cout << "Converting from Metadata" << std::endl;
        std::cout << "Number of transcripts: " << metadata->num_transcripts << std::endl;

        std::vector<CandidateTranscriptStub> transcripts = std::vector<CandidateTranscriptStub>(metadata->num_transcripts);
        for (int i = 0; i < metadata->num_transcripts; i++) {
            std::cout << "Converting transcript " << i << std::endl;
            const CandidateTranscript candidateTranscript = metadata->transcripts[i];
            std::cout << "Transcript confidence " << candidateTranscript.confidence << std::endl;
            CandidateTranscriptStub transcript = CandidateTranscriptStub::fromCandidateTranscript(candidateTranscript);
            std::cout << "Converted transcript confidence " << transcript.confidence << std::endl;
            transcripts[i] = transcript;
        }

        return MetadataStub{
            transcripts
        };
    }
} MetadataStub;

class Stream {
 public:
  Stream(StreamingState* streamingState)
    : streamingState(streamingState) {}

  void feedAudioContent(std::vector<short> audioBuffer) {
    STT_FeedAudioContent(this->streamingState, audioBuffer.data(), audioBuffer.size());
  }

  std::string intermediateDecode() {
    char* tempResult = STT_IntermediateDecode(this->streamingState);
    if (!tempResult) {
      // There was some error, return an empty string.
      return std::string();
    }

    // We must manually free the string if something was returned to us.
    std::string result = tempResult;
    STT_FreeString(tempResult);
    return result;
  }

  MetadataStub intermediateDecodeWithMetadata(unsigned int numResults = 1) {
    Metadata* tempResult =
      STT_IntermediateDecodeWithMetadata(this->streamingState, numResults);
    if (!tempResult) {
      // There was some error, return an empty string.
      return MetadataStub{};
    }

    MetadataStub metadata = MetadataStub::fromMetadata(tempResult);
    STT_FreeMetadata(tempResult);

    return metadata;
  }

  std::string intermediateDecodeFlushBuffers() {
    char* tempResult =
      STT_IntermediateDecodeFlushBuffers(this->streamingState);
    if (!tempResult) {
      // There was some error, return an empty string.
      return std::string();
    }

    // We must manually free the string if something was returned to us.
    std::string result = tempResult;
    STT_FreeString(tempResult);
    return result;
  }

  MetadataStub intermediateDecodeWithMetadataFlushBuffers(unsigned int numResults = 1) {
    Metadata* tempResult =
      STT_IntermediateDecodeWithMetadataFlushBuffers(this->streamingState, numResults);
    if (!tempResult) {
      // There was some error, return an empty string.
      return MetadataStub{};
    }

    MetadataStub metadata = MetadataStub::fromMetadata(tempResult);
    STT_FreeMetadata(tempResult);

    return metadata;
  }

  std::string finishStream() {
    char* tempResult = STT_FinishStream(this->streamingState);
    // Regardless of the result, the stream will be deleted.
    this->streamingState = nullptr;

    if (!tempResult) {
      // There was some error, return an empty string.
      return std::string();
    }

    // We must manually free the string if something was returned to us.
    std::string result = tempResult;
    STT_FreeString(tempResult);
    return result;
  }

  MetadataStub finishStreamWithMetadata(unsigned int numResults = 1) {
    Metadata* tempResult =
      STT_FinishStreamWithMetadata(this->streamingState, numResults);
    // Regardless of the result, the stream will be deleted.
    this->streamingState = nullptr;

    if (!tempResult) {
      // There was some error, return an empty string.
      return MetadataStub{};
    }

    MetadataStub metadata = MetadataStub::fromMetadata(tempResult);
    STT_FreeMetadata(tempResult);

    return metadata;
  }

 private:
  StreamingState* streamingState;
};

class Model {
 public:
  Model(std::string buffer) : state(nullptr), buffer(buffer) {
    loadModelFromBuffer();
  }

  ~Model() { STT_FreeModel(state); }

  int getSampleRate() const { return STT_GetModelSampleRate(this->state); }

  int getModelBeamWidth() const { return STT_GetModelBeamWidth(this->state); }

  void setModelBeamWidth(unsigned int width) const {
    int status = STT_SetModelBeamWidth(this->state, width);
    if (status != STT_ERR_OK) {
      char* error = STT_ErrorCodeToErrorMessage(status);
      std::cerr << "Could not set model beam width: " << error << std::endl;
      STT_FreeString(error);
    }
  }

  void freeModel() const { return STT_FreeModel(this->state); }

  void enableExternalScorer(std::string scorerBuffer) const {
    int status = STT_EnableExternalScorerFromBuffer(this->state, scorerBuffer.c_str(),
                                                    scorerBuffer.size());
    if (status != STT_ERR_OK) {
      char* error = STT_ErrorCodeToErrorMessage(status);
      std::cerr << "Could not enable external scorer: " << error << std::endl;
      STT_FreeString(error);
    }
  }

  void disableExternalScorer() const {
    int status = STT_DisableExternalScorer(this->state);
    if (status != STT_ERR_OK) {
      char* error = STT_ErrorCodeToErrorMessage(status);
      std::cerr << "Could not set model beam width: " << error << std::endl;
      STT_FreeString(error);
    }
  }

  void setScorerAlphaBeta(float alpha, float beta) const {
    int status = STT_SetScorerAlphaBeta(this->state, alpha, beta);
    if (status != STT_ERR_OK) {
      char* error = STT_ErrorCodeToErrorMessage(status);
      std::cerr << "Could not set scorer alpha beta: " << error << std::endl;
      STT_FreeString(error);
    }
  }

  void addHotWord(const std::string& word, float boost) {
    int status = STT_AddHotWord(this->state, word.c_str(), boost);
    if (status != STT_ERR_OK) {
      char* error = STT_ErrorCodeToErrorMessage(status);
      std::cerr << "Could not add hot word: " << error << std::endl;
      STT_FreeString(error);
    }
  }

  void eraseHotWord(const std::string& word) {
    int status = STT_EraseHotWord(this->state, word.c_str());
    if (status != STT_ERR_OK) {
      char* error = STT_ErrorCodeToErrorMessage(status);
      std::cerr << "Could not erase hot word: " << error << std::endl;
      STT_FreeString(error);
    }
  }

  void clearHotWords() {
    int status = STT_ClearHotWords(this->state);
    if (status != STT_ERR_OK) {
      char* error = STT_ErrorCodeToErrorMessage(status);
      std::cerr << "Could not clear hot words: " << error << std::endl;
      STT_FreeString(error);
    }
  }

  std::string speechToText(std::vector<short> audioBuffer) const {
    char* tempResult =
        STT_SpeechToText(this->state, audioBuffer.data(), audioBuffer.size());
    if (!tempResult) {
      // There was some error, return an empty string.
      return std::string();
    }

    // We must manually free the string if something was returned to us.
    std::string result = tempResult;
    STT_FreeString(tempResult);
    return result;
  }

  MetadataStub speechToTextWithMetadata(std::vector<short> audioBuffer,
                                       unsigned int aNumResults) const {
    Metadata* tempResult = STT_SpeechToTextWithMetadata(
        this->state, audioBuffer.data(), audioBuffer.size(), aNumResults);

    std::cout << "Metadata num_transcripts: " << tempResult->num_transcripts << std::endl;
    MetadataStub metadata = MetadataStub::fromMetadata(tempResult);
    std::cout << "MetadataStub num_transcripts: " << metadata.transcripts.size() << std::endl;
    STT_FreeMetadata(tempResult);

    return metadata;
  }

  Stream* createStream() {
    StreamingState* streamingState;
    int status = STT_CreateStream(this->state, &streamingState);
    if (status != STT_ERR_OK) {
      char* error = STT_ErrorCodeToErrorMessage(status);
      std::cerr << "createStream failed: " << error << std::endl;
      STT_FreeString(error);
      return nullptr;
    }

    return new Stream(streamingState);
  }

 private:
  ModelState* state;
  std::string buffer;

  void loadModelFromBuffer() {
    std::cout << "Loading model from buffer" << std::endl;
    int ret = STT_CreateModelFromBuffer(this->buffer.c_str(),
                                        this->buffer.size(), &this->state);
    if (ret != STT_ERR_OK) {
      char* error = STT_ErrorCodeToErrorMessage(ret);
      std::cerr << "Could not create model: " << error << std::endl;
      STT_FreeString(error);
      return;
    }
  }
};

// Binding code
EMSCRIPTEN_BINDINGS(coqui_ai_apis) {
  class_<Model>("Model")
      .constructor<std::string>()
      .function("getSampleRate", &Model::getSampleRate)
      .function("getModelBeamWidth", &Model::getModelBeamWidth)
      .function("setModelBeamWidth", &Model::setModelBeamWidth)
      .function("freeModel", &Model::freeModel)
      .function("addHotWord", &Model::addHotWord)
      .function("eraseHotWord", &Model::eraseHotWord)
      .function("clearHotWords", &Model::clearHotWords)
      .function("speechToText", &Model::speechToText)
      .function("speechToTextWithMetadata", &Model::speechToTextWithMetadata)
      .function("createStream", &Model::createStream, allow_raw_pointers())
      .function("enableExternalScorer", &Model::enableExternalScorer)
      .function("disableExternalScorer", &Model::disableExternalScorer)
      .function("setScorerAlphaBeta", &Model::setScorerAlphaBeta);

  class_<Stream>("Stream")
      .constructor<StreamingState*>()
      .function("feedAudioContent", &Stream::feedAudioContent)
      .function("intermediateDecode", &Stream::intermediateDecode)
      .function("intermediateDecodeWithMetadata", &Stream::intermediateDecodeWithMetadata)
      .function("intermediateDecodeFlushBuffers", &Stream::intermediateDecodeFlushBuffers)
      .function("intermediateDecodeWithMetadataFlushBuffers",
                &Stream::intermediateDecodeWithMetadataFlushBuffers)
      .function("finishStream", &Stream::finishStream)
      .function("finishStreamWithMetadata", &Stream::finishStreamWithMetadata);



  value_object<TokenMetadataStub>("TokenMetadataStub")
      .field("text", &TokenMetadataStub::text)
      .field("timestep", &TokenMetadataStub::timestep)
      .field("start_time", &TokenMetadataStub::start_time);

  value_object<CandidateTranscriptStub>("CandidateTranscriptStub")
      .field("tokens", &CandidateTranscriptStub::tokens)
      .field("confidence", &CandidateTranscriptStub::confidence);

  value_object<MetadataStub>("Metadata")
      .field("transcripts", &MetadataStub::transcripts);

  register_vector<short>("VectorShort");
  register_vector<CandidateTranscriptStub>("CandidateTranscriptStubVector");
  register_vector<TokenMetadataStub>("TokenMetadataStubVector");
}
