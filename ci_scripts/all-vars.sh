#!/bin/bash

set -xe

ROOT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." &> /dev/null && pwd)
CI_TASK_DIR=${CI_TASK_DIR:-${ROOT_DIR}}

export OS=$(uname)
if [ "${OS}" = "Linux" ]; then
    export DS_ROOT_TASK=${CI_TASK_DIR}
    export PYENV_ROOT="${DS_ROOT_TASK}/pyenv-root"
    export DS_CPU_COUNT=$(nproc)
fi;

if [ "${OS}" = "${CI_MSYS_VERSION}" ]; then
    export CI_TASK_DIR="$(cygpath ${CI_TASK_DIR})"
    export DS_ROOT_TASK=${CI_TASK_DIR}
    export PYENV_ROOT="${CI_TASK_DIR}/pyenv-root"
    export PLATFORM_EXE_SUFFIX=.exe
    export DS_CPU_COUNT=$(nproc)

    # Those are the versions available on NuGet.org
    export SUPPORTED_PYTHON_VERSIONS="3.5.4:ucs2 3.6.8:ucs2 3.7.6:ucs2 3.8.1:ucs2 3.9.0:ucs2"
fi;

if [ "${OS}" = "Darwin" ]; then
    export DS_ROOT_TASK=${CI_TASK_DIR}
    export DS_CPU_COUNT=$(sysctl hw.ncpu |cut -d' ' -f2)
    export PYENV_ROOT="${DS_ROOT_TASK}/pyenv-root"
fi

export CI_ARTIFACTS_DIR=${CI_ARTIFACTS_DIR:-${CI_TASK_DIR}/artifacts}
export CI_TMP_DIR=${CI_TMP_DIR:-/tmp}

export ANDROID_TMP_DIR=/data/local/tmp

mkdir -p ${CI_TMP_DIR} || true

export DS_TFDIR=${DS_ROOT_TASK}/tensorflow
export DS_DSDIR=${DS_ROOT_TASK}/
export DS_EXAMPLEDIR=${DS_ROOT_TASK}/examples

export DS_VERSION="$(cat ${DS_DSDIR}/training/coqui_stt_training/VERSION)"

export GRADLE_USER_HOME=${DS_ROOT_TASK}/gradle-cache
export ANDROID_SDK_HOME=${DS_ROOT_TASK}/STT/Android/SDK/
export ANDROID_NDK_HOME=${DS_ROOT_TASK}/STT/Android/android-ndk-r19c/

WGET=${WGET:-"wget"}
TAR=${TAR:-"tar"}
XZ=${XZ:-"xz -9 -T0"}
ZIP=${ZIP:-"zip"}
UNXZ=${UNXZ:-"xz -T0 -d"}
UNGZ=${UNGZ:-"gunzip"}

if [ "${OS}" = "Darwin" ]; then
  TAR="gtar"
fi

if [ "${OS}" = "${CI_MSYS_VERSION}" ]; then
  WGET=/usr/bin/wget.exe
  TAR=/usr/bin/tar.exe
  XZ="xz -9 -T0 -c -"
  UNXZ="xz -9 -T0 -d"
fi

model_source="${STT_TEST_MODEL}"
model_name="$(basename "${model_source}")"

ldc93s1_sample_filename=''
