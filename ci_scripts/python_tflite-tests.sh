#!/bin/bash

set -xe

source $(dirname "$0")/all-vars.sh
source $(dirname "$0")/all-utils.sh
source $(dirname "$0")/asserts.sh

samplerate=$1
ldc93s1_sample_filename="LDC93S1_pcms16le_1_${samplerate}.wav"

model_source=${STT_TEST_MODEL}
model_name=$(basename "${model_source}")
download_data

export_py_bin_path

which stt
stt --version

run_all_inference_tests

run_hotword_tests
