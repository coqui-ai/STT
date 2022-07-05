#!/bin/sh

# This test optimizes the scorer for testing purposes

set -xe

if [ ! -f lm_optimizer.py ]; then
    echo "Please make sure you run this from STT's top level directory."
    exit 1
fi;



lm_path="./data/lm"
sources_lm_filepath="./data/smoke_test/vocab.txt"

# Force only one visible device because we have a single-sample dataset
# and when trying to run on multiple devices (like GPUs), this will break

python data/lm/generate_lm_batch.py \
    --input_txt "${sources_lm_filepath}" \
    --output_dir "${lm_path}" \
    --top_k_list 30000-50000 \
    --arpa_order_list "1-2" \
    --max_arpa_memory "85%" \
    --arpa_prune_list "0|0|2" \
    --binary_a_bits 255 \
    --binary_q_bits 8 \
    --binary_type trie \
    --kenlm_bins /code/kenlm/build/bin/ \
    -j 1
