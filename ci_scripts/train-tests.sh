#!/bin/bash
set -xe

source $(dirname "$0")/all-vars.sh
source $(dirname "$0")/all-utils.sh

bitrate=$1
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
case "${bitrate}" in
    8k)
        sample_rate=8000
        sample_name='LDC93S1_pcms16le_1_8000.wav'
    ;;
    16k)
        sample_rate=16000
        sample_name='LDC93S1_pcms16le_1_16000.wav'
    ;;
esac

# Easier to rename to that we can exercize the LDC93S1 importer code to
# generate the CSV file.
echo "Moving ${sample_name} to LDC93S1.wav"
mv "data/smoke_test/${sample_name}" "data/smoke_test/LDC93S1.wav"

# Run twice to test preprocessed features
time ./bin/run-ci-ldc93s1_new.sh 249 "${sample_rate}"
time ./bin/run-ci-ldc93s1_new.sh 1 "${sample_rate}"
time ./bin/run-ci-ldc93s1_tflite.sh "${sample_rate}"

tar -cf - \
    -C /tmp/ckpt/ . \
    | ${XZ} > ${CI_ARTIFACTS_DIR}/checkpoint.tar.xz

cp /tmp/train/output_graph.pb ${CI_ARTIFACTS_DIR}
cp /tmp/train_tflite/output_graph.tflite ${CI_ARTIFACTS_DIR}

/tmp/convert_graphdef_memmapped_format --in_graph=/tmp/train/output_graph.pb --out_graph=/tmp/train/output_graph.pbmm
cp /tmp/train/output_graph.pbmm ${CI_ARTIFACTS_DIR}

time ./bin/run-ci-ldc93s1_checkpoint.sh
