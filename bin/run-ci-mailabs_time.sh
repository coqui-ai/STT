#!/bin/sh

set -xe

mailabs_dir=$1   #"./data/M-AILABS"
mailabs_lang=$2  #"fr_FR"
alphabet_path=$3 #"./data/fr_FR/alphabet.txt"
scorer_path=$4   #"./data/fr_FR/fr_lm.scorer"
mailabs_train_csv="${mailabs_dir}${mailabs_lang}/${mailabs_lang}_train.csv"
mailabs_dev_csv="${mailabs_dir}${mailabs_lang}/${mailabs_lang}_test.csv"
mailabs_test_csv="${mailabs_dir}${mailabs_lang}/${mailabs_lang}_test.csv"

epoch_count=1
audio_sample_rate=16000

if [ ! -f "${mailabs_train_csv}" ]; then
  echo "Downloading and preprocessing M-AILABS data, saving in ${mailabs_dir}${mailabs_lang}/."
  python -u bin/import_m-ailabs.py ${mailabs_dir} --language ${mailabs_lang}
fi

st=$(date +%s)
echo "Index 0 starts at ${st}."

python -u train.py --alphabet_config_path ${alphabet_path} \
  --show_progressbar false --early_stop false \
  --train_files ${mailabs_train_csv} --train_batch_size 32 \
  --feature_cache '/tmp/mailabs_cache' \
  --dev_files ${ldc93s1_csv} --dev_batch_size 32 \
  --test_files ${ldc93s1_csv} --test_batch_size 32 \
  --n_hidden 100 --epochs $epoch_count \
  --max_to_keep 1 --checkpoint_dir '/tmp/mailabs_ckpt' \
  --learning_rate 0.001 --dropout_rate 0.05 --export_dir '/tmp/mailabs_train' \
  --scorer_path ${scorer_path} \
  --audio_sample_rate ${audio_sample_rate} \
  --export_tflite false \
  --log_level 0

exit_code=$?

ent=$(date +%s)
echo "Index -1 ends at ${ent}"

ext=$(expr $ent - $st)
echo "Execution took ${ext} seconds to return exit code ${exit_code}."
