#!/bin/bash

set -xe

source $(dirname "$0")/all-vars.sh
source $(dirname "$0")/package-utils.sh

mkdir -p ${CI_ARTIFACTS_DIR} || true

cp ${DS_DSDIR}/tensorflow/bazel*.log ${CI_ARTIFACTS_DIR}/

package_native_client "native_client.tar.xz"

package_libstt_as_zip "libstt.zip"

if [ -d ${DS_DSDIR}/wheels ]; then
    cp ${DS_DSDIR}/wheels/* ${CI_ARTIFACTS_DIR}/
    cp ${DS_DSDIR}/native_client/javascript/stt-*.tgz ${CI_ARTIFACTS_DIR}/
fi;

if [ -f ${DS_DSDIR}/native_client/javascript/wrapper.tar.gz ]; then
    cp ${DS_DSDIR}/native_client/javascript/wrapper.tar.gz ${CI_ARTIFACTS_DIR}/
fi;
