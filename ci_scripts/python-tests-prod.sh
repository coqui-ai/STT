#!/bin/bash

set -xe

source $(dirname "$0")/all-vars.sh
source $(dirname "$0")/all-utils.sh
source $(dirname "$0")/asserts.sh

bitrate=$1
set_ldc_sample_filename "${bitrate}"

model_source=${STT_PROD_MODEL}
model_name=$(basename "${model_source}")

model_source_mmap=${STT_PROD_MODEL_MMAP}
model_name_mmap=$(basename "${model_source_mmap}")

download_model_prod

download_material

export_py_bin_path

which stt
stt --version

run_prod_inference_tests "${bitrate}"

run_prod_concurrent_stream_tests "${bitrate}"
