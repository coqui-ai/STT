#ifndef OUTPUT_H_
#define OUTPUT_H_

#include <vector>

/* Struct for the beam search output, containing the tokens based on the vocabulary indices, and the timesteps
 * for each token in the beam search output
 */
struct Output {
    double confidence;
    std::vector<unsigned int> tokens;
    std::vector<unsigned int> timesteps;
};

struct FlashlightOutput {
    double aggregate_score;
    double acoustic_model_score;
    double language_model_score;
    std::vector<std::string> words;
    std::vector<int> tokens;
};

#endif  // OUTPUT_H_
