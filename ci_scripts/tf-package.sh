#!/bin/bash

set -xe

source $(dirname $0)/tf-vars.sh

mkdir -p ${CI_ARTIFACTS_DIR} || true

OUTPUT_ROOT="${DS_ROOT_TASK}/tensorflow/bazel-bin"

for output_bin in                           \
    tensorflow/lite/libtensorflow.so        \
    tensorflow/lite/libtensorflow.so.if.lib \
    ;
do
    if [ -f "${OUTPUT_ROOT}/${output_bin}" ]; then
        cp ${OUTPUT_ROOT}/${output_bin} ${CI_ARTIFACTS_DIR}/
    fi;
done

# Make a tar of bazel caches
RELATIVE_CACHE_ROOT=$(realpath --relative-to="${DS_ROOT_TASK}" ${BAZEL_CACHE_ROOT})
if [ "${OS}" = "${CI_MSYS_VERSION}" ]; then
    export PATH=$PATH:'/c/Program Files/7-Zip/'
    pushd ${DS_ROOT_TASK}
        7z a -snl -snh -so home.tar ${RELATIVE_CACHE_ROOT} | 7z a -si ${CI_ARTIFACTS_DIR}/home.tar.xz
    popd
else
    ${TAR} -C ${DS_ROOT_TASK} -cf - ${RELATIVE_CACHE_ROOT} | ${XZ} > ${CI_ARTIFACTS_DIR}/home.tar.xz
fi

if [ "${OS}" = "Linux" ]; then
    SHA_SUM_GEN="sha256sum"
elif [ "${OS}" = "${CI_MSYS_VERSION}" ]; then
    SHA_SUM_GEN="sha256sum"
elif [ "${OS}" = "Darwin" ]; then
    SHA_SUM_GEN="shasum -a 256"
fi;

${SHA_SUM_GEN} ${CI_ARTIFACTS_DIR}/* > ${CI_ARTIFACTS_DIR}/checksums.txt
