#!/bin/bash

set -xe

source $(dirname "$0")/all-vars.sh
source $(dirname "$0")/all-utils.sh
source $(dirname "$0")/build-utils.sh

source $(dirname "$0")/tf-vars.sh

BAZEL_TARGETS="
//native_client:stt_ios
//native_client:kenlm_ios
//native_client:stt_swift
"

BAZEL_BUILD_FLAGS="${BAZEL_OPT_FLAGS} ${BAZEL_EXTRA_FLAGS}"

BAZEL_ENV_FLAGS="TF_NEED_CUDA=0"
SYSTEM_TARGET=

do_bazel_build
