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

    ${CURL} -sSL -o ${DS_ROOT_TASK}/dls/$fname $1 && echo "$2  ${DS_ROOT_TASK}/dls/$fname" | ${SHA_SUM} -
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
mkdir -p ${DS_ROOT_TASK}/bin || true

SUFFIX=""
if [ "${OS}" = "${CI_MSYS_VERSION}" ]; then
    SUFFIX=".exe"
fi

cp ${DS_ROOT_TASK}/dls/${BAZEL_INSTALL_FILENAME} ${DS_ROOT_TASK}/bin/bazel${SUFFIX}
chmod +x ${DS_ROOT_TASK}/bin/bazel${SUFFIX}

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
