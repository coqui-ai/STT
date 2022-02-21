#!/bin/bash
set -xe

source $(dirname "$0")/all-vars.sh
source $(dirname "$0")/all-utils.sh

time jupyter nbconvert --to notebook --execute notebooks/easy_transfer_learning.ipynb
time jupyter nbconvert --to notebook --execute notebooks/train_your_first_coqui_STT_model.ipynb
time jupyter nbconvert --to notebook --execute notebooks/train_with_common_voice.ipynb
