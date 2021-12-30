#!/bin/bash

set -e

if [ $# -eq 0 ]; then
    echo -e "\n This script prepares a controlled testing environment for OOV handling."
    echo -e "\n Usage: \n $0 <data.csv> <am_chechpoint_dir> <OOV percentage> \n"
    echo -e "\n Ex: $0 data.csv checkpoint-dir/ 0.1 \n"
    exit 1
fi

data=$1
am=$2
percent=${3:-0.1}

if awk -v x=$percent -v y=1 'BEGIN { exit (x >= y) ? 0 : 1 }'; then
    echo " Error: OOV percentage must be less than one."
    exit 0
fi

mkdir -p tmp/
mkdir -p tmp/lm

# Data preparation: split the vocab into 10% (that'd later represent OOVs)
# and the remaining 90% to compose a corpus for LM generation
echo "Preparing Data for Language Model Generation"

# Extract corpus vocabulary (unique words)
xsv select transcript $data | awk -F, '$3!="" && NR>1;{print $0}' > tmp/data.txt
sed 's/ /\n/g' tmp/data.txt | sort | uniq -c | sort -nr > tmp/vocab.txt

# Pick the least frequent 10% words to build OOV set
oov_count=$(wc -l tmp/vocab.txt | awk -v p="$percent" '{print int($0*p)}')
tail -$oov_count tmp/vocab.txt | awk '{print $2}'> tmp/oov_words
grep -wFf tmp/oov_words tmp/data.txt > tmp/oov_sents

# Exclude OOVs from the text corpus
grep -vf tmp/oov_sents tmp/data.txt > tmp/scorer_corpus.txt
gzip -c tmp/scorer_corpus.txt > tmp/scorer_corpus.txt.gz
grep -vf tmp/oov_sents $data > tmp/scorer_corpus.csv

# Prepare OOV CSV or testing purposes (to assess improvements on it)
grep -wFf tmp/oov_sents tmp/data.txt > tmp/oov_corpus.txt
echo "wav_filename,wav_filesize,transcript" > tmp/oov_corpus.csv
grep -wFf tmp/oov_sents $data >> tmp/oov_corpus.csv

# Generate LM
python3 data/lm/generate_lm.py --input_txt tmp/scorer_corpus.txt.gz \
    --output_dir tmp/lm --top_k 500000 --kenlm_bins kenlm/build/bin \
    --arpa_order 3 --max_arpa_memory "85%" --arpa_prune "0|0|1" \
    --binary_a_bits 255 --binary_q_bits 8 --binary_type trie --discount_fallback

./native_client/generate_scorer_package --alphabet $am/alphabet.txt \
    --lm tmp/lm/lm.binary --vocab tmp/lm/vocab-500000.txt \
    --package tmp/lm/kenlm.scorer --default_alpha 0.931289039105002 \
    --default_beta 1.1834137581510284

echo "Done!"
