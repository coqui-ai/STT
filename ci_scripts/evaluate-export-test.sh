#!/bin/bash
set -xe

source $(dirname "$0")/all-vars.sh
source $(dirname "$0")/all-utils.sh

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
cp "data/smoke_test/${sample_name}" "data/smoke_test/LDC93S1.wav"

# Evaluate tflite model on wav files
python bin/import_ldc93s1.py data/smoke_test
python -m coqui_stt_training.evaluate_export  --model $STT_TEST_MODEL --csv "data/smoke_test/ldc93s1.csv" --dump /tmp/result_wav
cat /tmp/result_wav.out

# Evaluate tflite model on opus files
opus_csv="data/smoke_test/ldc93s1_opus.csv"
opus_path=$(readlink -f data/smoke_test/LDC93S1.opus)
echo "wav_filename,wav_filesize,transcript" > $opus_csv
echo $opus_path",93638,she had your dark suit in greasy wash water all year" >> $opus_csv
python -m coqui_stt_training.evaluate_export  --model $STT_TEST_MODEL --csv $opus_csv --dump /tmp/result_opus
cat /tmp/result_opus.out
