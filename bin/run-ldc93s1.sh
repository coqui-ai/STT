#!/bin/sh
set -xe
if [ ! -f train.py ]; then
    echo "Please make sure you run this from STT's top level directory."
    exit 1
fi;

if [ ! -f "data/smoke_test/ldc93s1.csv" ]; then
    echo "Downloading and preprocessing LDC93S1 example data, saving in ./data/smoke_test."
    python -u bin/import_ldc93s1.py ./data/smoke_test
fi;

if [ -d "${COMPUTE_KEEP_DIR}" ]; then
    checkpoint_dir=$COMPUTE_KEEP_DIR
else
    checkpoint_dir=$(python -c 'from xdg import BaseDirectory as xdg; print(xdg.save_data_path("stt/ldc93s1"))')
fi

# Force only one visible device because we have a single-sample dataset
# and when trying to run on multiple devices (like GPUs), this will break
export CUDA_VISIBLE_DEVICES=0

python -m coqui_stt_training.train \
  --alphabet_config_path "data/alphabet.txt" \
  --show_progressbar false \
  --train_files data/smoke_test/ldc93s1.csv \
  --test_files data/smoke_test/ldc93s1.csv \
  --train_batch_size 1 \
  --test_batch_size 1 \
  --n_hidden 100 \
  --epochs 200 \
  --checkpoint_dir "$checkpoint_dir" \
  "$@"
