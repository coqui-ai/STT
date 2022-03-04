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

BAZEL_BUILD_FLAGS="--config=android_x86_64 ${BAZEL_EXTRA_FLAGS}"
SYSTEM_TARGET=
SYSTEM_RASPBIAN=

do_bazel_build

do_stt_ndk_build "x86_64"
