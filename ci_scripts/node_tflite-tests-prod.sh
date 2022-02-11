#!/bin/bash

set -xe

source $(dirname "$0")/all-vars.sh
source $(dirname "$0")/all-utils.sh
source $(dirname "$0")/asserts.sh

<<<<<<< HEAD
bitrate=$1
set_ldc_sample_filename "${bitrate}"
=======
<<<<<<< HEAD
bitrate=$1
set_ldc_sample_filename "${bitrate}"
=======
samplerate=$1
ldc93s1_sample_filename="LDC93S1_pcms16le_1_${samplerate}.wav"
>>>>>>> coqui-ai-main
>>>>>>> 94b13b64c30dd1349c6e325dba22877620ef914b

model_source=${STT_PROD_MODEL}
model_name=$(basename "${model_source}")
download_model_prod

download_data

node --version
npm --version

export_node_bin_path

check_runtime_nodejs

<<<<<<< HEAD
run_prodtflite_inference_tests "${bitrate}"

run_js_streaming_prodtflite_inference_tests "${bitrate}"
=======
<<<<<<< HEAD
run_prodtflite_inference_tests "${bitrate}"

run_js_streaming_prodtflite_inference_tests "${bitrate}"
=======
run_prodtflite_inference_tests "${samplerate}"

run_js_streaming_prodtflite_inference_tests "${samplerate}"
>>>>>>> coqui-ai-main
>>>>>>> 94b13b64c30dd1349c6e325dba22877620ef914b
