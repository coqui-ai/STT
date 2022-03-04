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

BAZEL_BUILD_FLAGS="--config=ios_arm64 ${BAZEL_EXTRA_FLAGS}"
SYSTEM_TARGET=

do_bazel_build
