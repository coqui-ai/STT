#!/bin/bash

set -xe

do_bazel_build()
{
  local _opt_or_dbg=${1:-"opt"}

  cd ${DS_TFDIR}

  unset EMSDK_PYTHON
  
  echo "**** DEBUG trying to understand which python"
  which -a python
  which -a python3
  echo "**** DEBUG Should have shown pythons on path"

  bazel build ${BAZEL_CACHE} \
    --action_env=PATH=/tmp/venv/bin:$PATH \
    -s --explain bazel_explain.log --verbose_explanations \
    --workspace_status_command="bash native_client/bazel_workspace_status_cmd.sh" \
    -c ${_opt_or_dbg} ${BAZEL_BUILD_FLAGS} ${BAZEL_TARGETS}

  ls -lh bazel-bin/native_client

  if [ "${_opt_or_dbg}" = "opt" ]; then
    verify_bazel_rebuild "${DS_ROOT_TASK}/tensorflow/bazel_explain.log"
  fi
}

shutdown_bazel()
{
  cd ${DS_TFDIR}
  bazel shutdown
}

do_stt_binary_build()
{
  cd ${DS_DSDIR}
  $MAKE -C native_client/ \
    TARGET=${SYSTEM_TARGET} \
    TFDIR=${DS_TFDIR} \
    RASPBIAN=${SYSTEM_RASPBIAN} \
    EXTRA_CFLAGS="${EXTRA_LOCAL_CFLAGS}" \
    EXTRA_LDFLAGS="${EXTRA_LOCAL_LDFLAGS}" \
    EXTRA_LIBS="${EXTRA_LOCAL_LIBS}" \
    stt${PLATFORM_EXE_SUFFIX}
}

do_stt_ndk_build()
{
  arch_abi=$1

  cd ${DS_DSDIR}/native_client/

  ${ANDROID_NDK_HOME}/ndk-build \
    APP_PLATFORM=android-21 \
    APP_BUILD_SCRIPT=$(pwd)/Android.mk \
    NDK_PROJECT_PATH=$(pwd) \
    APP_STL=c++_shared \
    TFDIR=${DS_TFDIR} \
    TARGET_ARCH_ABI=${arch_abi}
}
