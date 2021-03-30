#!/bin/bash

set -xe

source $(dirname "$0")/all-vars.sh
source $(dirname "$0")/all-utils.sh
source $(dirname "$0")/asserts.sh

bitrate=$1
set_ldc_sample_filename "${bitrate}"

model_source=${STT_PROD_MODEL//.pb/.tflite}
model_name=$(basename "${model_source}")
model_source_mmap=${STT_PROD_MODEL_MMAP//.pbmm/.tflite}
model_name_mmap=$(basename "${model_source}")

download_model_prod

download_data

node --version
npm --version

symlink_electron

export_node_bin_path

which electron
which node

node --version

stt --version

check_runtime_electronjs

run_electronjs_prodtflite_inference_tests "${bitrate}"
