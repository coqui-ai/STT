#!/bin/bash

set -xe

source $(dirname "$0")/all-vars.sh
source $(dirname "$0")/package-utils.sh

mkdir -p ${CI_ARTIFACTS_DIR} || true

cp ${DS_DSDIR}/tensorflow/bazel*.log ${CI_ARTIFACTS_DIR}/

arm_flavor=$1

package_native_client_ndk "native_client.tar.xz" "${arm_flavor}"
