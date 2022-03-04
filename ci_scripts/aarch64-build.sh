#!/bin/bash

set -xe

source $(dirname "$0")/all-vars.sh
source $(dirname "$0")/all-utils.sh
source $(dirname "$0")/build-utils.sh

source $(dirname "$0")/tf-vars.sh

BAZEL_TARGETS="
//native_client:libstt.so
//native_client:libkenlm.so
//native_client:generate_scorer_package
"

BAZEL_BUILD_FLAGS="--config=elinux_aarch64 ${BAZEL_EXTRA_FLAGS}"

do_bazel_build

do_stt_binary_build
