#!/bin/bash

set -xe

source $(dirname "$0")/all-vars.sh
source $(dirname "$0")/all-utils.sh
source $(dirname "$0")/asserts.sh

bitrate=$1
set_ldc_sample_filename "${bitrate}"

model_source=${STT_PROD_MODEL}
model_name=$(basename "${model_source}")
download_model_prod

download_data

node --version
npm --version

export_node_bin_path

check_runtime_nodejs

run_prodtflite_inference_tests "${bitrate}"

run_js_streaming_prodtflite_inference_tests "${bitrate}"
