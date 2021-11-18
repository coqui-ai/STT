#!/usr/bin/env python
import os
from import_ldc93s1 import _download_and_preprocess_data as download_ldc
from coqui_stt_training.util.config import initialize_globals_from_args
from coqui_stt_training.train import train
from coqui_stt_training.evaluate import test

# only one GPU for only one training sample
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

download_ldc("data/smoke_test")

initialize_globals_from_args(
    load_train="init",
    alphabet_config_path="data/alphabet.txt",
    train_files=["data/smoke_test/ldc93s1.csv"],
    dev_files=["data/smoke_test/ldc93s1.csv"],
    test_files=["data/smoke_test/ldc93s1.csv"],
    augment=["time_mask"],
    n_hidden=100,
    epochs=200,
)

train()
test()
