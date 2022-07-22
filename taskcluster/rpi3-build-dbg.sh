#!/bin/bash

set -xe

source $(dirname "$0")/tc-tests-utils.sh

source $(dirname "$0")/tf_tc-vars.sh

BAZEL_TARGETS="
//native_client:libstt.so
"

BAZEL_BUILD_FLAGS="${BAZEL_ARM_FLAGS} ${BAZEL_EXTRA_FLAGS}"
BAZEL_ENV_FLAGS="TF_NEED_CUDA=0"
SYSTEM_TARGET=rpi3
SYSTEM_RASPBIAN=/tmp/multistrap-raspbian-bullseye

maybe_install_xldd

do_bazel_build "dbg"

export EXTRA_LOCAL_CFLAGS="-ggdb"
do_deepspeech_binary_build
