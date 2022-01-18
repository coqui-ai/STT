#!/bin/bash
set -xe

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
source ${SCRIPT_DIR}/all-vars.sh
source ${SCRIPT_DIR}/all-utils.sh

samplerate=$1
decoder_src=$2
if [ "$decoder_src" != "--pypi" ]; then
    # Use decoder package built in this CI group
    export DS_NODECODER=1
fi

mkdir -p /tmp/train || true
mkdir -p /tmp/train_tflite || true

set -o pipefail
python -m pip install --upgrade pip setuptools wheel | cat
python -m pip install --upgrade . | cat
set +o pipefail

# Prepare correct arguments for training
case "${samplerate}" in
    8000)
        sample_name='LDC93S1_pcms16le_1_8000.wav'
    ;;
    16000)
        sample_name='LDC93S1_pcms16le_1_16000.wav'
    ;;
esac

# Easier to rename to that we can exercize the LDC93S1 importer code to
# generate the CSV file.
echo "Moving ${sample_name} to LDC93S1.wav"
mv "data/smoke_test/${sample_name}" "data/smoke_test/LDC93S1.wav"
