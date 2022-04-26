#!/bin/sh

# This test optimizes the scorer for testing purposes

set -xe

if [ ! -f lm_optimizer.py ]; then
    echo "Please make sure you run this from STT's top level directory."
    exit 1
fi;

LM_ALPHA_MAX=1
LM_BETA_MAX=1
LM_NUM_TRIALS=1

scorer_filepath="./data/smoke_test/pruned_lm.scorer"
test_filepath="./data/smoke_test/ldc93s1_flac.csv"

checkpoint_dir="${HOME}/.local/share/stt/ldc93s1"

# Force only one visible device because we have a single-sample dataset
# and when trying to run on multiple devices (like GPUs), this will break
export CUDA_VISIBLE_DEVICES=0

python -m coqui_stt_training.util.lm_optimize \
        --scorer_path $scorer_filepath \
        --checkpoint_dir "$checkpoint_dir" \
        --test_files $test_filepath \
        --n_trials $LM_NUM_TRIALS \
        --lm_alpha_max ${LM_ALPHA_MAX} \
        --lm_beta_max ${LM_BETA_MAX} \
        --feature_cache /tmp/lm_feature_cache \
        "$@"
