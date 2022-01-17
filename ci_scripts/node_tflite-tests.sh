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

node --version
npm --version

export_node_bin_path

check_runtime_nodejs

run_all_inference_tests

run_js_streaming_inference_tests

run_hotword_tests
