#!/bin/bash

set -xe

package_native_client()
{
  tensorflow_dir=${DS_TFDIR}
  stt_dir=${DS_DSDIR}
  artifacts_dir=${CI_ARTIFACTS_DIR}
  artifact_name=$1

  if [ ! -d ${tensorflow_dir} -o ! -d ${stt_dir} -o ! -d ${artifacts_dir} ]; then
    echo "Missing directory. Please check:"
    echo "tensorflow_dir=${tensorflow_dir}"
    echo "stt_dir=${stt_dir}"
    echo "artifacts_dir=${artifacts_dir}"
    exit 1
  fi;

  if [ -z "${artifact_name}" ]; then
    echo "Please specify artifact name."
  fi;

  win_lib=""
  if [ -f "${tensorflow_dir}/bazel-bin/native_client/libstt.so.if.lib" ]; then
    win_lib="-C ${tensorflow_dir}/bazel-bin/native_client/ libstt.so.if.lib"
  fi;

  if [ -f "${tensorflow_dir}/bazel-bin/native_client/libkenlm.so.if.lib" ]; then
    win_lib="$win_lib -C ${tensorflow_dir}/bazel-bin/native_client/ libkenlm.so.if.lib"
  fi;

  libsox_lib=""
  if [ -f "${stt_dir}/sox-build/lib/libsox.so.3" ]; then
    libsox_lib="-C ${stt_dir}/sox-build/lib libsox.so.3"
  fi

  ${TAR} --verbose -cf - \
    --transform='flags=r;s|README.coqui|KenLM_License_Info.txt|' \
    -C ${tensorflow_dir}/bazel-bin/native_client/ libstt.so \
    -C ${tensorflow_dir}/bazel-bin/native_client/ libkenlm.so \
    ${win_lib} \
    ${libsox_lib} \
    -C ${tensorflow_dir}/bazel-bin/native_client/ generate_scorer_package \
    -C ${stt_dir}/ LICENSE \
    -C ${stt_dir}/native_client/ stt${PLATFORM_EXE_SUFFIX} \
    -C ${stt_dir}/native_client/ coqui-stt.h \
    -C ${stt_dir}/native_client/kenlm/ README.coqui \
    | ${XZ} > "${artifacts_dir}/${artifact_name}"
}

package_native_client_ndk()
{
  stt_dir=${DS_DSDIR}
  tensorflow_dir=${DS_TFDIR}
  artifacts_dir=${CI_ARTIFACTS_DIR}
  artifact_name=$1
  arch_abi=$2

  if [ ! -d ${stt_dir} -o ! -d ${artifacts_dir} ]; then
    echo "Missing directory. Please check:"
    echo "stt_dir=${stt_dir}"
    echo "artifacts_dir=${artifacts_dir}"
    exit 1
  fi;

  if [ -z "${artifact_name}" ]; then
    echo "Please specify artifact name."
  fi;

  if [ -z "${arch_abi}" ]; then
    echo "Please specify arch abi."
  fi;

  ${TAR} --verbose -cf - \
    -C ${stt_dir}/native_client/libs/${arch_abi}/ stt \
    -C ${stt_dir}/native_client/libs/${arch_abi}/ libstt.so \
    -C ${stt_dir}/native_client/libs/${arch_abi}/ libkenlm.so \
    -C ${tensorflow_dir}/bazel-bin/native_client/ generate_scorer_package \
    -C ${stt_dir}/native_client/libs/${arch_abi}/ libc++_shared.so \
    -C ${stt_dir}/native_client/ coqui-stt.h \
    -C ${stt_dir}/ LICENSE \
    -C ${stt_dir}/native_client/kenlm/ README.coqui \
    | ${XZ} > "${artifacts_dir}/${artifact_name}"
}

package_libstt_as_zip()
{
  tensorflow_dir=${DS_TFDIR}
  stt_dir=${DS_DSDIR}
  artifacts_dir=${CI_ARTIFACTS_DIR}
  artifact_name=$1

  if [ ! -d ${tensorflow_dir} -o ! -d ${artifacts_dir} ]; then
    echo "Missing directory. Please check:"
    echo "tensorflow_dir=${tensorflow_dir}"
    echo "artifacts_dir=${artifacts_dir}"
    exit 1
  fi;

  if [ -z "${artifact_name}" ]; then
    echo "Please specify artifact name."
  fi;

  libsox_lib=""
  if [ -f "${stt_dir}/sox-build/lib/libsox.so.3" ]; then
    libsox_lib="${stt_dir}/sox-build/lib/libsox.so.3"
  fi

  ${ZIP} -r9 --junk-paths "${artifacts_dir}/${artifact_name}" \
    ${tensorflow_dir}/bazel-bin/native_client/libstt.so \
    ${tensorflow_dir}/bazel-bin/native_client/libkenlm.so \
    ${libsox_lib}
}

package_libstt_wasm()
{
  tensorflow_dir=${DS_TFDIR}
  stt_dir=${DS_DSDIR}
  artifacts_dir=${CI_ARTIFACTS_DIR}
  artifact_name=$1

  if [ ! -d ${tensorflow_dir} -o ! -d ${artifacts_dir} ]; then
    echo "Missing directory. Please check:"
    echo "tensorflow_dir=${tensorflow_dir}"
    echo "artifacts_dir=${artifacts_dir}"
    exit 1
  fi;

  if [ -z "${artifact_name}" ]; then
    echo "Please specify artifact name."
  fi;

  ${ZIP} -r9 --junk-paths "${artifacts_dir}/${artifact_name}" \
    ${stt_dir}/native_client/kenlm/COPYING \
    ${tensorflow_dir}/bazel-bin/native_client/stt_wasm_bindings/stt_wasm.js \
    ${tensorflow_dir}/bazel-bin/native_client/stt_wasm_bindings/stt_wasm.worker.js \
    ${tensorflow_dir}/bazel-bin/native_client/stt_wasm_bindings/stt_wasm.wasm
}
