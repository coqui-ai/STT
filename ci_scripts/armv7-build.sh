#!/bin/bash

set -xe

source $(dirname "$0")/all-vars.sh
source $(dirname "$0")/all-utils.sh
source $(dirname "$0")/build-utils.sh

source $(dirname "$0")/tf-vars.sh

BAZEL_TARGETS="
//native_client:libstt.so
//native_client:generate_scorer_package
"

BAZEL_BUILD_FLAGS="${BAZEL_ARM_FLAGS} ${BAZEL_EXTRA_FLAGS}"
BAZEL_ENV_FLAGS="TF_NEED_CUDA=0"

<<<<<<< HEAD
maybe_install_xldd

=======
<<<<<<< HEAD
maybe_install_xldd

=======
>>>>>>> coqui-ai-main
>>>>>>> 94b13b64c30dd1349c6e325dba22877620ef914b
do_bazel_build

do_stt_binary_build
