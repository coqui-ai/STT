#!/bin/bash

set -xe

download_model_prod()
{
  local _model_source_file=$(basename "${model_source}")
  ${WGET} "${model_source}" -O - | gunzip --force > "${CI_TMP_DIR}/${_model_source_file}"
}

download_data()
{
  cp ${DS_DSDIR}/data/smoke_test/*.wav ${CI_TMP_DIR}/
  cp ${DS_DSDIR}/data/smoke_test/pruned_lm.scorer ${CI_TMP_DIR}/kenlm.scorer
  cp ${DS_DSDIR}/data/smoke_test/pruned_lm.bytes.scorer ${CI_TMP_DIR}/kenlm.bytes.scorer

  cp -R ${DS_DSDIR}/native_client/test ${CI_TMP_DIR}/test_sources
}

download_material()
{
  download_data

  ls -hal ${CI_TMP_DIR}/${model_name} ${CI_TMP_DIR}/LDC93S1*.wav
}

verify_bazel_rebuild()
{
  bazel_explain_file="$1"

  if [ ! -f "${bazel_explain_file}" ]; then
    echo "No such explain file: ${bazel_explain_file}"
    exit 1
  fi;

  mkdir -p ${CI_ARTIFACTS_DIR} || true

  cp ${DS_DSDIR}/tensorflow/bazel*.log ${CI_ARTIFACTS_DIR}/

  spurious_rebuilds=$(grep 'Executing action' "${bazel_explain_file}" | grep 'Compiling' | grep -v -E 'no entry in the cache|[for host]|unconditional execution is requested|Executing genrule //native_client:workspace_status|Compiling native_client/workspace_status.cc|Linking native_client/libstt.so' | wc -l)
  if [ "${spurious_rebuilds}" -ne 0 ]; then
    echo "Bazel rebuilds some file it should not, please check."

    if is_patched_bazel; then
      mkdir -p ${DS_ROOT_TASK}/ckd/ds ${DS_ROOT_TASK}/ckd/tf
      tar xf ${DS_ROOT_TASK}/bazel-ckd-tf.tar --strip-components=4 -C ${DS_ROOT_TASK}/ckd/ds/
      tar xf ${DS_ROOT_TASK}/bazel-ckd-ds.tar --strip-components=4 -C ${DS_DSDIR}/ckd/tensorflow/

      echo "Making a diff between CKD files"
      mkdir -p ${CI_ARTIFACTS_DIR}
      diff -urNw ${DS_DSDIR}/ckd/tensorflow/ ${DS_ROOT_TASK}/ckd/ds/ | tee ${CI_ARTIFACTS_DIR}/ckd.diff

      rm -fr ${DS_DSDIR}/ckd/tensorflow/ ${DS_ROOT_TASK}/ckd/ds/
    else
      echo "Cannot get CKD information from release, please use patched Bazel"
    fi;

    exit 1
  fi;
}

symlink_electron()
{
  if [ "${OS}" = "Darwin" ]; then
    ln -s Electron.app/Contents/MacOS/Electron node_modules/electron/dist/node
  else
    ln -s electron "${DS_ROOT_TASK}/node_modules/electron/dist/node"

    if [ "${OS}" = "Linux" -a -f "${DS_ROOT_TASK}/node_modules/electron/dist/chrome-sandbox" ]; then
      export ELECTRON_DISABLE_SANDBOX=1
    fi
  fi
}

export_node_bin_path()
{
  export PATH=${DS_ROOT_TASK}/node_modules/.bin/:${DS_ROOT_TASK}/node_modules/electron/dist/:$PATH
}

export_py_bin_path()
{
  export PATH=$HOME/.local/bin/:$PATH
}
