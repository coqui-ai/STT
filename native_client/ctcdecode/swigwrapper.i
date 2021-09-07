%module swigwrapper

%{
#include "ctc_beam_search_decoder.h"
#define SWIG_FILE_WITH_INIT
#define SWIG_PYTHON_STRICT_BYTE_CHAR
#include "workspace_status.h"
%}

%include <pyabc.i>
%include <std_string.i>
%include <std_vector.i>
%include <std_shared_ptr.i>
%include <std_unordered_map.i>
%include "numpy.i"

%init %{
import_array();
%}

namespace std {
    %template(StringVector) vector<string>;
    %template(FloatVector) vector<float>;
    %template(UnsignedIntVector) vector<unsigned int>;
    %template(OutputVector) vector<Output>;
    %template(OutputVectorVector) vector<vector<Output>>;
    %template(FlashlightOutputVector) vector<FlashlightOutput>;
    %template(FlashlightOutputVectorVector) vector<vector<FlashlightOutput>>;
    %template(Map) unordered_map<string, float>;
}

%shared_ptr(Scorer);

// Convert NumPy arrays to pointer+lengths
%apply (double* IN_ARRAY2, int DIM1, int DIM2) {(const double *probs, int time_dim, int class_dim)};
%apply (double* IN_ARRAY3, int DIM1, int DIM2, int DIM3) {(const double *probs, int batch_size, int time_dim, int class_dim)};
%apply (int* IN_ARRAY1, int DIM1) {(const int *seq_lengths, int seq_lengths_size)};
%apply (unsigned int* IN_ARRAY1, int DIM1) {(const unsigned int *input, int length)};

%ignore Scorer::dictionary;

%include "third_party/flashlight/flashlight/lib/text/dictionary/Dictionary.h"
%include "../alphabet.h"
%include "output.h"
%include "scorer.h"
%include "ctc_beam_search_decoder.h"

%constant const char* __version__ = ds_version();
%constant const char* __git_version__ = ds_git_version();

// Import only the error code enum definitions from coqui-stt.h
#define SWIG_ERRORS_ONLY
%include "../coqui-stt.h"
