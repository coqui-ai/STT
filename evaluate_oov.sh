#!/bin/bash
set -e


if [ $# -eq 0 ]; then
    echo "\n This script compares the performance of a given AM on both OOV and non-OOV testing sets with the use of an external scorer."
    echo "\n It works on the data prepared by oov_lm_prep.sh"
    echo -e "\n Usage: \n $0 <am_chechpoint_dir> <scorer> \n"
    exit 1
fi

am=$1
scorer=tmp/lm/kenlm.scorer
nj=$(nproc)

mkdir -p tmp/results

echo "Evaluating Using Scorer"

echo "Case (1): Evaluating on OOV testing set."
python -m coqui_stt_training.evaluate --test_files tmp/oov_corpus.csv \
    --test_output_file tmp/results/oov_results.json --scorer_path $scorer \
    --checkpoint_dir $am --test_batch_size $nj

echo "Case (2): Evaluating on original testing set."
python -m coqui_stt_training.evaluate --test_files tmp/scorer_corpus.csv \
    --test_output_file tmp/results/samples.json --scorer_path $scorer \
    --checkpoint_dir $am --test_batch_size $nj
