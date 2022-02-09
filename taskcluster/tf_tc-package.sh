#!/bin/bash

set -xe

source $(dirname $0)/tf_tc-vars.sh

mkdir -p ${TASKCLUSTER_ARTIFACTS} || true

cp ${DS_ROOT_TASK}/tensorflow/bazel_*.log ${TASKCLUSTER_ARTIFACTS} || true

OUTPUT_ROOT="${DS_ROOT_TASK}/tensorflow/bazel-bin"

for output_bin in                                                            \
    tensorflow/lite/experimental/c/libtensorflowlite_c.so                    \
    tensorflow/tools/graph_transforms/transform_graph                        \
    tensorflow/tools/graph_transforms/summarize_graph                        \
    tensorflow/tools/benchmark/benchmark_model                               \
    tensorflow/contrib/util/convert_graphdef_memmapped_format                \
    tensorflow/lite/toco/toco;
do
    if [ -f "${OUTPUT_ROOT}/${output_bin}" ]; then
        cp ${OUTPUT_ROOT}/${output_bin} ${TASKCLUSTER_ARTIFACTS}/
    fi;
done;

if [ -f "${OUTPUT_ROOT}/tensorflow/lite/tools/benchmark/benchmark_model" ]; then
    cp ${OUTPUT_ROOT}/tensorflow/lite/tools/benchmark/benchmark_model ${TASKCLUSTER_ARTIFACTS}/lite_benchmark_model
fi

# It seems that bsdtar and gnutar are behaving a bit differently on the way
# they deal with --exclude="./public/*" ; this caused ./DeepSpeech/tensorflow/core/public/
# to be ditched when we just wanted to get rid of ./public/ on OSX.
# Switching to gnutar (already needed for the --transform on DeepSpeech tasks)
# does the trick.
TAR_EXCLUDE="--exclude=./dls/*"
if [ "${OS}" = "Darwin" ]; then
    TAR_EXCLUDE="--exclude=./dls/* --exclude=./public/* --exclude=./generic-worker/* --exclude=./homebrew/* --exclude=./homebrew.cache/* --exclude=./homebrew.logs/*"
fi;

# Make a tar of
#  - /home/build-user/ (linux
#  - /Users/build-user/TaskCluster/HeavyTasks/X/ (OSX)
#  - C:\builds\tc-workdir\ (windows)

if [ "${OS}" = "${TC_MSYS_VERSION}" ]; then
    export PATH=$PATH:'/c/Program Files/7-Zip/'
    pushd ${DS_ROOT_TASK}
        7z a '-xr!.\dls\' '-xr!.\tmp\' '-xr!.\msys64\' -snl -snh -so home.tar . | 7z a -si ${TASKCLUSTER_ARTIFACTS}/home.tar.xz
    popd
else
    ${TAR} -C ${DS_ROOT_TASK} ${TAR_EXCLUDE} -cf - . | ${XZ} > ${TASKCLUSTER_ARTIFACTS}/home.tar.xz
fi

if [ "${OS}" = "Linux" ]; then
    SHA_SUM_GEN="sha256sum"
elif [ "${OS}" = "${TC_MSYS_VERSION}" ]; then
    SHA_SUM_GEN="sha256sum"
elif [ "${OS}" = "Darwin" ]; then
    SHA_SUM_GEN="shasum -a 256"
fi;

${SHA_SUM_GEN} ${TASKCLUSTER_ARTIFACTS}/* > ${TASKCLUSTER_ARTIFACTS}/checksums.txt
