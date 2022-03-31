#!/bin/bash

set -xe

macos_target_arch=$1
SYSTEM_TARGET=host
if [ "$(uname)-$(uname -m)" = "Darwin-x86_64" -a "${macos_target_arch}" = "arm64" ]; then
  SYSTEM_TARGET="darwin-arm64"
fi

source $(dirname "$0")/all-vars.sh
source $(dirname "$0")/all-utils.sh
source $(dirname "$0")/build-utils.sh

source $(dirname "$0")/tf-vars.sh

BAZEL_TARGETS="//native_client:generate_scorer_package"
WORKSPACE_STATUS=" "

BAZEL_BUILD_FLAGS="${BAZEL_OPT_FLAGS} ${BAZEL_EXTRA_FLAGS}"

do_bazel_build
