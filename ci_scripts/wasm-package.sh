#!/bin/bash

set -xe

source $(dirname "$0")/all-vars.sh
source $(dirname "$0")/package-utils.sh

mkdir -p ${CI_ARTIFACTS_DIR} || true

cp ${DS_DSDIR}/tensorflow/bazel*.log ${CI_ARTIFACTS_DIR}/

package_libstt_wasm "libstt.zip"
