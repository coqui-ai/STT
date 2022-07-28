#!/bin/bash

set -xe

source $(dirname "$0")/all-vars.sh
source $(dirname "$0")/all-utils.sh
source $(dirname "$0")/build-utils.sh

source $(dirname "$0")/tf-vars.sh

BAZEL_TARGETS="
//native_client:stt_wasm_bindings
"

BAZEL_OPT_FLAGS="--copt=-pthread --copt=-fexceptions"
# Bazel caching and emsdk do not play nice together: unless path
# is explicitly passed, emsdk would end up using an old version of
# Python which does not support f-strings, making build fail.
BAZEL_EXTRA_FLAGS="${BAZEL_EXTRA_FLAGS} ${BAZEL_WASM_EXTRA_FLAGS} --action_env=PATH"
BAZEL_BUILD_FLAGS="${BAZEL_OPT_FLAGS} ${BAZEL_EXTRA_FLAGS}"
SYSTEM_TARGET=

do_bazel_build
