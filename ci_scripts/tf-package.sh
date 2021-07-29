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

# It seems that bsdtar and gnutar are behaving a bit differently on the way
# they deal with --exclude="./public/*" ; this caused ./STT/tensorflow/core/public/
# to be ditched when we just wanted to get rid of ./public/ on OSX.
# Switching to gnutar (already needed for the --transform on STT tasks)
# does the trick.
TAR_EXCLUDE="--exclude=./dls/*"
if [ "${OS}" = "Darwin" ]; then
    TAR_EXCLUDE="--exclude=./dls/* --exclude=./public/* --exclude=./generic-worker/* --exclude=./homebrew/* --exclude=./homebrew.cache/* --exclude=./homebrew.logs/*"
fi;

# Make a tar of
#  - /home/build-user/ (linux
#  - /Users/build-user/TaskCluster/HeavyTasks/X/ (OSX)
#  - C:\builds\tc-workdir\ (windows)

if [ "${OS}" = "${CI_MSYS_VERSION}" ]; then
    export PATH=$PATH:'/c/Program Files/7-Zip/'
    pushd ${DS_ROOT_TASK}
        7z a '-xr!.\dls\' '-xr!.\tmp\' '-xr!.\msys64\' -snl -snh -so home.tar . | 7z a -si ${CI_ARTIFACTS_DIR}/home.tar.xz
    popd
else
    ${TAR} -C ${DS_ROOT_TASK} ${TAR_EXCLUDE} -cf - . | ${XZ} > ${CI_ARTIFACTS_DIR}/home.tar.xz
fi

if [ "${OS}" = "Linux" ]; then
    SHA_SUM_GEN="sha256sum"
elif [ "${OS}" = "${CI_MSYS_VERSION}" ]; then
    SHA_SUM_GEN="sha256sum"
elif [ "${OS}" = "Darwin" ]; then
    SHA_SUM_GEN="shasum -a 256"
fi;

${SHA_SUM_GEN} ${CI_ARTIFACTS_DIR}/* > ${CI_ARTIFACTS_DIR}/checksums.txt
