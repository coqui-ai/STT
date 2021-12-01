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
python -m pip install --upgrade ".[transcribe]" | cat
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

# Testing single SDB source
time ./bin/run-ci-ldc93s1_new_sdb.sh 220 "${sample_rate}"
# Testing interleaved source (SDB+CSV combination) - run twice to test preprocessed features
time ./bin/run-ci-ldc93s1_new_sdb_csv.sh 109 "${sample_rate}"
time ./bin/run-ci-ldc93s1_new_sdb_csv.sh 1 "${sample_rate}"

# Test --metrics_files training argument
time ./bin/run-ci-ldc93s1_new_metrics.sh 2 "${sample_rate}"

# Test training with bytes output mode
time ./bin/run-ci-ldc93s1_new_bytes.sh 200 "${sample_rate}"
time ./bin/run-ci-ldc93s1_new_bytes_tflite.sh "${sample_rate}"

tar -cf - \
    -C /tmp/ckpt/ . \
    | ${XZ} > ${CI_ARTIFACTS_DIR}/checkpoint.tar.xz

# Save exported model artifacts from bytes output mode training
cp /tmp/train_bytes/output_graph.pb ${CI_ARTIFACTS_DIR}/output_graph.pb
cp /tmp/train_bytes_tflite/output_graph.tflite ${CI_ARTIFACTS_DIR}/output_graph.tflite

/tmp/convert_graphdef_memmapped_format --in_graph=/tmp/train_bytes/output_graph.pb --out_graph=/tmp/train_bytes/output_graph.pbmm
cp /tmp/train_bytes/output_graph.pbmm ${CI_ARTIFACTS_DIR}

# Test resuming from checkpoints created above
# SDB, resuming from checkpoint
time ./bin/run-ci-ldc93s1_checkpoint_sdb.sh

# Bytes output mode, resuming from checkpoint
time ./bin/run-ci-ldc93s1_checkpoint_bytes.sh

# Training with args set via initialize_globals_from_args()
time python ./bin/run-ldc93s1.py

# Training graph inference
time ./bin/run-ci-ldc93s1_singleshotinference.sh

# transcribe module
time python -m coqui_stt_training.transcribe \
    --src "data/smoke_test/LDC93S1.wav" \
    --dst ${CI_ARTIFACTS_DIR}/transcribe.log \
    --n_hidden 100 \
    --scorer_path "data/smoke_test/pruned_lm.scorer"

mkdir /tmp/transcribe_dir
cp data/smoke_test/LDC93S1.wav /tmp/transcribe_dir
time python -m coqui_stt_training.transcribe \
   --src "/tmp/transcribe_dir/" \
   --n_hidden 100 \
   --scorer_path "data/smoke_test/pruned_lm.scorer"

for i in /tmp/transcribe_dir/*.tlog; do echo $i; cat $i; echo; done
