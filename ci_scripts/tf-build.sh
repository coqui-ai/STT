#!/bin/bash

set -ex
set -o pipefail

source $(dirname $0)/tf-vars.sh

pushd ${DS_ROOT_TASK}/tensorflow/
    BAZEL_BUILD="bazel ${BAZEL_OUTPUT_USER_ROOT} build -s"

    MAYBE_DEBUG=$2
    OPT_OR_DBG="-c opt"
    if [ "${MAYBE_DEBUG}" = "dbg" ]; then
        OPT_OR_DBG="-c dbg"
    fi;

    case "$1" in
    "--windows-cpu")
        echo "" | TF_NEED_CUDA=0 ./configure && ${BAZEL_BUILD} ${OPT_OR_DBG} ${BAZEL_OPT_FLAGS} ${BAZEL_EXTRA_FLAGS} ${BUILD_TARGET_LITE_LIB}
        ;;
    "--linux-cpu"|"--darwin-cpu")
        echo "" | TF_NEED_CUDA=0 ./configure && ${BAZEL_BUILD} ${OPT_OR_DBG} ${BAZEL_OPT_FLAGS} ${BAZEL_EXTRA_FLAGS} ${BUILD_TARGET_LITE_LIB}
        ;;
    "--linux-armv7")
        echo "" | TF_NEED_CUDA=0 ./configure && ${BAZEL_BUILD} ${OPT_OR_DBG} ${BAZEL_ARM_FLAGS} ${BAZEL_EXTRA_FLAGS} ${BUILD_TARGET_LITE_LIB}
        ;;
    "--linux-aarch64")
        echo "" | TF_NEED_CUDA=0 ./configure && ${BAZEL_BUILD} ${OPT_OR_DBG} ${BAZEL_ARM64_FLAGS} ${BAZEL_EXTRA_FLAGS} ${BUILD_TARGET_LITE_LIB}
        ;;
    "--android-armv7")
        echo "" | TF_SET_ANDROID_WORKSPACE=1 ./configure && ${BAZEL_BUILD} ${OPT_OR_DBG} ${BAZEL_ANDROID_ARM_FLAGS} ${BAZEL_EXTRA_FLAGS} ${BUILD_TARGET_LITE_LIB}
        ;;
    "--android-arm64")
        echo "" | TF_SET_ANDROID_WORKSPACE=1 ./configure && ${BAZEL_BUILD} ${OPT_OR_DBG} ${BAZEL_ANDROID_ARM64_FLAGS} ${BAZEL_EXTRA_FLAGS} ${BUILD_TARGET_LITE_LIB}
        ;;
    "--ios-arm64")
        echo "" | TF_NEED_CUDA=0 TF_CONFIGURE_IOS=1 ./configure && ${BAZEL_BUILD} ${OPT_OR_DBG} ${BAZEL_IOS_ARM64_FLAGS} ${BUILD_TARGET_LITE_LIB}
        ;;
    "--ios-x86_64")
        echo "" | TF_NEED_CUDA=0 TF_CONFIGURE_IOS=1 ./configure && ${BAZEL_BUILD} ${OPT_OR_DBG} ${BAZEL_IOS_X86_64_FLAGS} ${BUILD_TARGET_LITE_LIB}
        ;;
    esac
popd
