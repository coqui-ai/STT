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

model_source=${STT_TEST_MODEL//.pb/.tflite}
model_name=$(basename "${model_source}")
export DATA_TMP_DIR=${CI_TMP_DIR}

download_material "${CI_TMP_DIR}/ds"

export PATH=${CI_TMP_DIR}/ds/:$PATH

check_versions

run_tflite_basic_inference_tests
