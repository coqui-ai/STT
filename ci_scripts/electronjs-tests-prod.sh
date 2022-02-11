#!/bin/bash

set -xe

source $(dirname "$0")/all-vars.sh
source $(dirname "$0")/all-utils.sh
source $(dirname "$0")/asserts.sh

bitrate=$1
set_ldc_sample_filename "${bitrate}"

model_source=${DEEPSPEECH_PROD_MODEL}
model_name=$(basename "${model_source}")
model_source_mmap=${DEEPSPEECH_PROD_MODEL_MMAP}
model_name_mmap=$(basename "${model_source_mmap}")

download_model_prod

download_data

node --version
npm --version

symlink_electron

export_node_bin_path

which electron
which node

node --version

deepspeech --version

check_runtime_electronjs

run_prod_inference_tests "${bitrate}"
