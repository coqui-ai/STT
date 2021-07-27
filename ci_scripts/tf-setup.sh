#!/bin/bash

set -ex

source $(dirname $0)/tf-vars.sh

install_android=
case "$1" in
    "--android-armv7"|"--android-arm64")
    install_android=yes
    ;;
esac

# $1 url
# $2 sha256
download()
{
    fname=`basename $1`

    ${WGET} $1 -O ${DS_ROOT_TASK}/dls/$fname && echo "$2  ${DS_ROOT_TASK}/dls/$fname" | ${SHA_SUM} -
}

# Download stuff
mkdir -p ${DS_ROOT_TASK}/dls || true
download $BAZEL_URL $BAZEL_SHA256

if [ ! -z "${install_android}" ]; then
    download $ANDROID_NDK_URL $ANDROID_NDK_SHA256
    download $ANDROID_SDK_URL $ANDROID_SDK_SHA256
fi;

# For debug
ls -hal ${DS_ROOT_TASK}/dls/

# Install Bazel in ${DS_ROOT_TASK}/bin
BAZEL_INSTALL_FILENAME=$(basename "${BAZEL_URL}")
if [ "${OS}" = "Linux" ]; then
    BAZEL_INSTALL_FLAGS="--user"
elif [ "${OS}" = "Darwin" ]; then
    BAZEL_INSTALL_FLAGS="--bin=${DS_ROOT_TASK}/bin --base=${DS_ROOT_TASK}/.bazel"
fi;
mkdir -p ${DS_ROOT_TASK}/bin || true
pushd ${DS_ROOT_TASK}/bin
    if [ "${OS}" = "${CI_MSYS_VERSION}" ]; then
        cp ${DS_ROOT_TASK}/dls/${BAZEL_INSTALL_FILENAME} ${DS_ROOT_TASK}/bin/bazel.exe
    else
        /bin/bash ${DS_ROOT_TASK}/dls/${BAZEL_INSTALL_FILENAME} ${BAZEL_INSTALL_FLAGS}
    fi
popd

# For debug
bazel version

bazel shutdown

if [ ! -z "${install_android}" ]; then
    mkdir -p ${DS_ROOT_TASK}/STT/Android/SDK || true
    ANDROID_NDK_FILE=`basename ${ANDROID_NDK_URL}`
    ANDROID_SDK_FILE=`basename ${ANDROID_SDK_URL}`

    pushd ${DS_ROOT_TASK}/STT/Android
        unzip ${DS_ROOT_TASK}/dls/${ANDROID_NDK_FILE}
    popd

    pushd ${DS_ROOT_TASK}/STT/Android/SDK
        unzip ${DS_ROOT_TASK}/dls/${ANDROID_SDK_FILE}
        yes | ./tools/bin/sdkmanager --licenses
        ./tools/bin/sdkmanager --update
        ./tools/bin/sdkmanager --install "platforms;android-16" "build-tools;28.0.3"
    popd
fi

mkdir -p ${CI_ARTIFACTS_DIR} || true


# Taken from https://www.tensorflow.org/install/source
# Only future is needed for our builds, as we don't build the Python package
python -m pip install -U --user future==0.17.1 || true
