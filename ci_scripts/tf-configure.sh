#!/bin/bash

set -ex
set -o pipefail

source $(dirname $0)/tf-vars.sh

pushd ${DS_ROOT_TASK}/tensorflow/
    case "$1" in
    "--android")
        echo "" | TF_SET_ANDROID_WORKSPACE=1 ./configure
        ;;
    "--ios")
        echo "" | TF_CONFIGURE_IOS=1 ./configure
        ;;
    esac
popd
