#!/bin/sh

set -xe

ldc93s1_dir="./data/smoke_test"
ldc93s1_csv="${ldc93s1_dir}/ldc93s1.csv"

if [ ! -f "${ldc93s1_dir}/ldc93s1.csv" ]; then
    echo "Downloading and preprocessing LDC93S1 example data, saving in ${ldc93s1_dir}."
    python -u bin/import_ldc93s1.py ${ldc93s1_dir}
fi;

# Force only one visible device because we have a single-sample dataset
# and when trying to run on multiple devices (like GPUs), this will break
export CUDA_VISIBLE_DEVICES=0

python -u train.py --alphabet_config_path "data/alphabet.txt" \
  --show_progressbar false --early_stop false \
  --train_files ${ldc93s1_csv} --train_batch_size 1 \
  --scorer "" \
  --augment dropout \
            pitch \
            tempo \
            warp \
            time_mask \
            frequency_mask \
            add \
            multiply \
  --n_hidden 100 \
  --epochs 1
