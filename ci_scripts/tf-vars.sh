#!/bin/bash

set -ex

export OS=$(uname)
if [ "${OS}" = "Linux" ]; then
    export DS_ROOT_TASK=${CI_TASK_DIR}

    BAZEL_URL=https://github.com/bazelbuild/bazelisk/releases/download/v1.10.1/bazelisk-linux-amd64
    BAZEL_SHA256=4cb534c52cdd47a6223d4596d530e7c9c785438ab3b0a49ff347e991c210b2cd

    ANDROID_NDK_URL=https://dl.google.com/android/repository/android-ndk-r18b-linux-x86_64.zip
    ANDROID_NDK_SHA256=4f61cbe4bbf6406aa5ef2ae871def78010eed6271af72de83f8bd0b07a9fd3fd

    ANDROID_SDK_URL=https://dl.google.com/android/repository/sdk-tools-linux-4333796.zip
    ANDROID_SDK_SHA256=92ffee5a1d98d856634e8b71132e8a95d96c83a63fde1099be3d86df3106def9

    WGET=/usr/bin/wget
elif [ "${OS}" = "${CI_MSYS_VERSION}" ]; then
    if [ -z "${CI_TASK_DIR}" -o -z "${CI_ARTIFACTS_DIR}" ]; then
        echo "Inconsistent Windows setup: missing some vars."
        echo "CI_TASK_DIR=${CI_TASK_DIR}"
        echo "CI_ARTIFACTS_DIR=${CI_ARTIFACTS_DIR}"
        exit 1
    fi;

    # Re-export with cygpath to make sure it is sane, otherwise it might trigger
    # unobvious failures with cp etc.
    export CI_TASK_DIR="$(cygpath ${CI_TASK_DIR})"
    export CI_ARTIFACTS_DIR="$(cygpath ${CI_ARTIFACTS_DIR})"

    export DS_ROOT_TASK=${CI_TASK_DIR}
    export BAZEL_VC="C:\Program Files (x86)\Microsoft Visual Studio\2019\Enterprise\VC"
    export BAZEL_VC_FULL_VERSION="14.29.30133"
    export MSYS2_ARG_CONV_EXCL='//'

    mkdir -p ${CI_TASK_DIR}/tmp/
    export TEMP=${CI_TASK_DIR}/tmp/
    export TMP=${CI_TASK_DIR}/tmp/

    BAZEL_URL=https://github.com/bazelbuild/bazelisk/releases/download/v1.10.1/bazelisk-windows-amd64.exe
    BAZEL_SHA256=9a89e6a8cc0a3aea37affcf8c146d8925ffbda1d2290c0c6a845ea81e05de62c

    TAR=/usr/bin/tar.exe
elif [ "${OS}" = "Darwin" ]; then
    if [ -z "${CI_TASK_DIR}" -o -z "${CI_ARTIFACTS_DIR}" ]; then
        echo "Inconsistent OSX setup: missing some vars."
        echo "CI_TASK_DIR=${CI_TASK_DIR}"
        echo "CI_ARTIFACTS_DIR=${CI_ARTIFACTS_DIR}"
        exit 1
    fi;

    export DS_ROOT_TASK=${CI_TASK_DIR}

    BAZEL_URL=https://github.com/bazelbuild/bazelisk/releases/download/v1.10.1/bazelisk-darwin-amd64
    BAZEL_SHA256=e485bbf84532d02a60b0eb23c702610b5408df3a199087a4f2b5e0995bbf2d5a

    SHA_SUM="shasum -a 256 -c"
    TAR=gtar
fi;

WGET=${WGET:-"wget"}
CURL=${CURL:-"curl"}
TAR=${TAR:-"tar"}
XZ=${XZ:-"xz -9 -T0"}
ZIP=${ZIP:-"zip"}
UNXZ=${UNXZ:-"xz -T0 -d"}
UNGZ=${UNGZ:-"gunzip"}
SHA_SUM=${SHA_SUM:-"sha256sum -c --strict"}

# /tmp/artifacts for docker-worker on linux,
# and task subdir for generic-worker on osx
export CI_ARTIFACTS_DIR=${CI_ARTIFACTS_DIR:-/tmp/artifacts}

### Define variables that needs to be exported to other processes

PATH=${DS_ROOT_TASK}/bin:$PATH
if [ "${OS}" = "Darwin" ]; then
    PATH=${DS_ROOT_TASK}/homebrew/bin/:${DS_ROOT_TASK}/homebrew/opt/node@10/bin:$PATH
fi;
export PATH

if [ "${OS}" = "Linux" ]; then
    export ANDROID_SDK_HOME=${DS_ROOT_TASK}/STT/Android/SDK/
    export ANDROID_NDK_HOME=${DS_ROOT_TASK}/STT/Android/android-ndk-r18b/
fi;

export TF_ENABLE_XLA=0
if [ "${OS}" = "Linux" ]; then
    TF_NEED_JEMALLOC=1
elif [ "${OS}" = "${CI_MSYS_VERSION}" ]; then
    TF_NEED_JEMALLOC=0
elif [ "${OS}" = "Darwin" ]; then
    TF_NEED_JEMALLOC=0
fi;
export TF_NEED_JEMALLOC
export TF_NEED_OPENCL_SYCL=0
export TF_NEED_MKL=0
export TF_NEED_VERBS=0
export TF_NEED_MPI=0
export TF_NEED_IGNITE=0
export TF_NEED_GDR=0
export TF_NEED_NGRAPH=0
export TF_DOWNLOAD_CLANG=0
export TF_SET_ANDROID_WORKSPACE=0
export TF_NEED_TENSORRT=0
export TF_NEED_ROCM=0

# This should be gcc-5, hopefully. CUDA and TensorFlow might not be happy, otherwise.
export GCC_HOST_COMPILER_PATH=/usr/bin/gcc

if [ "${OS}" = "Linux" ]; then
    source /etc/os-release
    if [ "${ID}" = "debian" -a "${VERSION_ID}" = "9" ]; then
        export PYTHON_BIN_PATH=/opt/python/cp37-cp37m/bin/python
    fi
elif [ "${OS}" != "${TC_MSYS_VERSION}" ]; then
    export PYTHON_BIN_PATH=python
fi

## Below, define or export some build variables

# Enable some SIMD support. Limit ourselves to what Tensorflow needs.
# Also ensure to not require too recent CPU: AVX2/FMA introduced by:
#  - Intel with Haswell (2013)
#  - AMD with Excavator (2015)
# For better compatibility, AVX ony might be better.
#
# Build for generic amd64 platforms, no device-specific optimization
# See https://gcc.gnu.org/onlinedocs/gcc/x86-Options.html for targetting specific CPUs

if [ "${OS}" = "${CI_MSYS_VERSION}" ]; then
    OPT_FLAGS="/arch:AVX"
else
    OPT_FLAGS="-mtune=generic -march=x86-64 -msse -msse2 -msse3 -msse4.1 -msse4.2 -mavx"
fi
BAZEL_OPT_FLAGS=""
for flag in ${OPT_FLAGS};
do
    BAZEL_OPT_FLAGS="${BAZEL_OPT_FLAGS} --copt=${flag}"
done;

BAZEL_OUTPUT_CACHE_DIR="${DS_ROOT_TASK}/.bazel_cache/"
BAZEL_OUTPUT_CACHE_INSTANCE="${BAZEL_OUTPUT_CACHE_DIR}/output/"
mkdir -p ${BAZEL_OUTPUT_CACHE_INSTANCE} || true

# We need both to ensure stable path ; default value for output_base is some
# MD5 value.
BAZEL_OUTPUT_USER_ROOT="--output_user_root ${BAZEL_OUTPUT_CACHE_DIR} --output_base ${BAZEL_OUTPUT_CACHE_INSTANCE}"
export BAZEL_OUTPUT_USER_ROOT

NVCC_COMPUTE="3.5"

BAZEL_ARM_FLAGS="--config=rpi3_opt"
BAZEL_ARM64_FLAGS="--config=rpi3-armv8_opt"
BAZEL_ANDROID_ARM_FLAGS="--config=android_arm"
BAZEL_ANDROID_ARM64_FLAGS="--config=android_arm64"
BAZEL_ANDROID_X86_64_FLAGS="--config=android_x86_64"
BAZEL_IOS_ARM64_FLAGS="--config=ios_arm64"
BAZEL_IOS_X86_64_FLAGS="--config=ios_x86_64"

if [ "${OS}" != "${CI_MSYS_VERSION}" ]; then
    BAZEL_EXTRA_FLAGS="--config=noaws --config=nogcp --config=nohdfs --config=nonccl"
fi

if [ "${OS}" = "Darwin" ]; then
    BAZEL_EXTRA_FLAGS="${BAZEL_EXTRA_FLAGS} --macos_minimum_os 10.10 --macos_sdk_version 10.15"
fi

### Define build targets that we will re-ues in sourcing scripts.
BUILD_TARGET_LIB_CPP_API="//tensorflow:tensorflow_cc"
BUILD_TARGET_LITE_LIB="//tensorflow/lite:libtensorflowlite.so"
BUILD_TARGET_LIBSTT="//native_client:libstt.so"
