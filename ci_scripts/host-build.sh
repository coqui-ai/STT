#!/bin/bash

set -xe

macos_arch=$1

source $(dirname "$0")/all-vars.sh
source $(dirname "$0")/all-utils.sh
source $(dirname "$0")/build-utils.sh

source $(dirname "$0")/tf-vars.sh

BAZEL_TARGETS="
//native_client:libstt.so
//native_client:generate_scorer_package
"

BAZEL_BUILD_FLAGS="${BAZEL_OPT_FLAGS} ${BAZEL_EXTRA_FLAGS}"
if [ "${OS}" = "Darwin" ]; then
  if [ "${macos_arch}" = "arm64" ]; then
    BAZEL_BUILD_FLAGS="${BAZEL_OPT_FLAGS_MACOS_ARM64} ${BAZEL_EXTRA_FLAGS_MACOS_ARM64}"
    EXTRA_LOCAL_CFLAGS="-mmacosx-version-min=11.0 -target arm64-apple-macos11 -DNO_SOX"
    EXTRA_LOCAL_LDFLAGS="-mmacosx-version-min=11.0 -target arm64-apple-macos11"
  else
    BAZEL_BUILD_FLAGS="${BAZEL_OPT_FLAGS_MACOS_X86_64} ${BAZEL_EXTRA_FLAGS_MACOS_X86_64}"
    EXTRA_LOCAL_CFLAGS="-mmacosx-version-min=10.10 -target x86_64-apple-macos10.10"
    EXTRA_LOCAL_LDFLAGS="-mmacosx-version-min=10.10 -target x86_64-apple-macos10.10"
  fi
fi

BAZEL_ENV_FLAGS="TF_NEED_CUDA=0"
SYSTEM_TARGET=host

do_bazel_build

do_stt_binary_build
