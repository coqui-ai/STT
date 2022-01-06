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

symlink_electron

export_node_bin_path

which electron
which node

if [ "${OS}" = "Linux" ]; then
  export DISPLAY=':99.0'
  sudo Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &
  xvfb_process=$!
fi

node --version

stt --version

check_runtime_electronjs

run_electronjs_prodtflite_inference_tests "${bitrate}"

if [ "${OS}" = "Linux" ]; then
  sleep 1
  sudo kill -9 ${xvfb_process} || true
fi
