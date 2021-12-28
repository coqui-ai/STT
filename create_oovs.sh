#!/bin/bash

set -e

stag=1

if [  $# -eq 0 ] ; then
	echo "\n This script prepares a controlled testing environment for OOV handling."
	echo -e "\n Usage: \n $0 <data.csv> \n"
	exit 1
fi

step=1
data=$1
nj=$(nproc)
mkdir -p tmp/
mkdir -p tmp/lm
mkdir -p tmp/results

# Data preparation: split the vocab into 10% (that'd later represent OOVs)
# and the remaining 90% to compose a corpus for LM generation
echo "Step 1: Preparing Data"
if [ $step -le 1 ] ;  then

	# Extract corpus unique vocabularies
	xsv select transcript $data > tmp/data.txt
	sed 's/ /\n/g' tmp/data.txt | sort | uniq -c | sort -nr > tmp/vocab.txt
        grep -o . tmp/vocab.txt  | sort -u > tmp/alphabet.txt

 	# Pick the least frequent 10% vocabularies to represent OOVs
	oov_count=$(wc tmp/vocab.txt | awk '{print int($0*0.1)}')
	tail -$oov_count tmp/vocab.txt | awk '{print $2}'> tmp/oov_words
	grep -wFf tmp/oov_words tmp/data.txt > tmp/oov_sents

	# Exclude OOVs from the text corpus
	grep -vf tmp/oov_sents tmp/data.txt > tmp/scorer_corpus.txt
	gzip -c tmp/scorer_corpus.txt > tmp/scorer_corpus.txt.gz
        grep -vf tmp/oov_sents $data > tmp/scorer_corpus.csv

	# Prepare OOV csv for testing purposes (to assess imporvements on it)
        grep -wFf tmp/oov_sents tmp/data.txt > tmp/oov_corpus.txt
        grep -wFf tmp/oov_sents $data | sed '1 i\wav_filename,wav_filesize,transcript' > tmp/oov_corpus.csv

fi

# Generate LM
echo "Step 2: Generaing Language Model"
if [ $step -le 2 ] ;  then

	python3 data/lm/generate_lm.py --input_txt tmp/scorer_corpus.txt.gz \
	--output_dir tmp/lm --top_k 500000 --kenlm_bins kenlm/build/bin \
	--arpa_order 5 --max_arpa_memory "85%" --arpa_prune "0|0|1" \
       	--binary_a_bits 255 --binary_q_bits 8 --binary_type trie --discount_fallback

        ./native_client/generate_scorer_package --alphabet tmp/alphabet.txt \
        --lm  tmp/lm/lm.binary --vocab tmp/lm/vocab-500000.txt \
        --package kenlm.scorer --default_alpha 0.931289039105002 \
        --default_beta 1.1834137581510284
fi

# Evaluate
echo "Step 3: Evaluating using scorer"
if [ $step -le 3 ] ; then
        echo "Evaluating on OOV testing set."
	python -m coqui_stt_training.evaluate --test_files tmp/oov_corpus.csv \
	--test_output_file tmp/results/oov_results.json --scorer_path native_client/kenlm.scorer \
        --checkpoint_dir /home/aya/work/tmp/AM/coqui-stt-1.1.0-checkpoint --test_batch_size $nj

	echo "Evaluating on original testing set."
	python -m coqui_stt_training.evaluate --test_files tmp/scorer_corpus.csv \
        --test_output_file tmp/results/samples.json --scorer_path native_client/kenlm.scorer \
        --checkpoint_dir /home/aya/work/tmp/AM/coqui-stt-1.1.0-checkpoint --test_batch_size $nj

fi
