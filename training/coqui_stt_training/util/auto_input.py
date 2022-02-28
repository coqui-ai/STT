#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pathlib import Path
from typing import Optional

import pandas
from tqdm import tqdm

from .io import open_remote
from .sample_collections import samples_from_sources
from coqui_stt_ctcdecoder import Alphabet


def create_alphabet_from_sources(sources: [str]) -> ([str], Alphabet):
    """Generate an Alphabet from characters in given sources.

    sources: List of paths to input sources (CSV, SDB).

    Returns a 2-tuple with list of characters and Alphabet instance.
    """
    characters = set()
    for sample in tqdm(samples_from_sources(sources)):
        characters |= set(sample.transcript)
    characters = list(sorted(characters))
    alphabet = Alphabet()
    alphabet.InitFromLabels(characters)
    return characters, alphabet


def _get_sample_size(population_size):
    """calculates the sample size for a 99% confidence and 1% margin of error"""
    margin_of_error = 0.01
    fraction_picking = 0.50
    z_score = 2.58  # Corresponds to confidence level 99%
    numerator = (z_score**2 * fraction_picking * (1 - fraction_picking)) / (
        margin_of_error**2
    )
    sample_size = 0
    for train_size in range(population_size, 0, -1):
        denominator = 1 + (z_score**2 * fraction_picking * (1 - fraction_picking)) / (
            margin_of_error**2 * train_size
        )
        sample_size = int(numerator / denominator)
        if 2 * sample_size + train_size <= population_size:
            break
    return sample_size


def _split_sets(samples: pandas.DataFrame, sample_size):
    """
    randomply split the datasets into train, validation, and test sets where the size of the
    validation and test sets are determined by the `get_sample_size` function.
    """
    samples = samples.sample(frac=1).reset_index(drop=True)

    train_beg = 0
    train_end = len(samples) - 2 * sample_size

    dev_beg = train_end
    dev_end = train_end + sample_size

    test_beg = dev_end
    test_end = len(samples)

    return (
        samples[train_beg:train_end],
        samples[dev_beg:dev_end],
        samples[test_beg:test_end],
    )


def create_datasets_from_auto_input(
    auto_input_dataset: Path, alphabet_config_path: Optional[Path]
) -> (Path, Path, Path, Path):
    """Creates training datasets from --auto_input_dataset flag.

    auto_input_dataset: Path to input CSV or folder containing CSV.

    Returns paths to generated train set, dev set and test set, and the path
    to the alphabet file, either generated from the data, existing alongside
    data, or specified manually by the user.
    """
    if auto_input_dataset.is_dir():
        auto_input_dir = auto_input_dataset
        all_csvs = list(auto_input_dataset.glob("*.csv"))
        if not all_csvs:
            raise RuntimeError(
                "--auto_input_dataset is a directory but no CSV file was found "
                "inside of it. Either make sure a CSV file is in the directory "
                "or specify the file it directly."
            )

        non_subsets = [f for f in all_csvs if f.stem not in ("train", "dev", "test")]
        if len(non_subsets) == 1:
            auto_input_csv = non_subsets[0]
        elif len(non_subsets) > 1:
            non_subsets_fmt = ", ".join(str(s) for s in non_subsets)
            raise RuntimeError(
                "--auto_input_dataset is a directory but there are multiple CSV "
                f"files not matching a subset name (train/dev/test): {non_subsets_fmt}. "
                "Either remove extraneous CSV files or specify the correct file "
                "to use for dataset formatting directly instead of the directory."
            )
        # else (empty) -> fall through, sets already present and get picked up below
    else:
        auto_input_dir = auto_input_dataset.parent
        auto_input_csv = auto_input_dataset

    train_set_path = auto_input_dir / "train.csv"
    dev_set_path = auto_input_dir / "dev.csv"
    test_set_path = auto_input_dir / "test.csv"

    if train_set_path.exists() != dev_set_path.exists() != test_set_path.exists():
        raise RuntimeError(
            "Specifying --auto_input_dataset with some generated files present "
            "and some missing. Either all three sets (train.csv, dev.csv, test.csv) "
            "should exist alongside {auto_input_csv} (in which case they will be used), "
            "or none of those files should exist (in which case they will be generated.)"
        )

    print(f"I Processing --auto_input_dataset input: {auto_input_csv}...")
    df = pandas.read_csv(auto_input_csv)

    if set(df.columns) < set(("wav_filename", "wav_filesize", "transcript")):
        raise RuntimeError(
            "Missing columns in --auto_input_dataset CSV. STT training inputs "
            "require wav_filename, wav_filesize, and transcript columns."
        )

    dev_test_size = _get_sample_size(len(df))
    if dev_test_size == 0:
        if len(df) >= 2:
            dev_test_size = 1
        else:
            raise RuntimeError(
                "--auto_input_dataset dataset is too small for automatic splitting "
                "into sets. Specify a larger input dataset or split it manually."
            )

    data_characters = sorted(list(set("".join(df["transcript"].values))))
    alphabet_alongside_data_path = auto_input_dir / "alphabet.txt"
    if alphabet_config_path:
        alphabet = Alphabet(str(alphabet_config_path))
        if not alphabet.CanEncode("".join(data_characters)):
            raise RuntimeError(
                "--alphabet_config_path was specified alongside --auto_input_dataset, "
                "but alphabet contents don't match dataset transcripts. Make sure the "
                "alphabet covers all transcripts or leave --alphabet_config_path "
                "unspecified so that one will be generated automatically."
            )
        print(f"I Using specified --alphabet_config_path: {alphabet_config_path}")
        generated_alphabet_path = alphabet_config_path
    elif alphabet_alongside_data_path.exists():
        alphabet = Alphabet(str(alphabet_alongside_data_path))
        if not alphabet.CanEncode("".join(data_characters)):
            raise RuntimeError(
                "alphabet.txt exists alongside --auto_input_dataset file, but "
                "alphabet contents don't match dataset transcripts. Make sure the "
                "alphabet covers all transcripts or remove alphabet.txt file "
                "from the data folderso that one will be generated automatically."
            )
        generated_alphabet_path = alphabet_alongside_data_path
        print(f"I Using existing alphabet file: {alphabet_alongside_data_path}")
    else:
        alphabet = Alphabet()
        alphabet.InitFromLabels(data_characters)
        generated_alphabet_path = auto_input_dir / "alphabet.txt"
        print(
            f"I Saved generated alphabet with characters ({data_characters}) into {generated_alphabet_path}"
        )
        with open_remote(str(generated_alphabet_path), "wb") as fout:
            fout.write(alphabet.SerializeText())

    # If splits don't already exist, generate and save them.
    # We check above that all three splits either exist or don't exist together,
    # so we can check a single one for existence here.
    if not train_set_path.exists():
        train_set, dev_set, test_set = _split_sets(df, dev_test_size)
        print(f"I Generated train set size: {len(train_set)} samples.")
        print(f"I Generated validation set size: {len(dev_set)} samples.")
        print(f"I Generated test set size: {len(test_set)} samples.")

        print(f"I Writing train set to {train_set_path}")
        train_set.to_csv(train_set_path, index=False)

        print(f"I Writing dev set to {dev_set_path}")
        dev_set.to_csv(dev_set_path, index=False)

        print(f"I Writing test set to {test_set_path}")
        test_set.to_csv(test_set_path, index=False)
    else:
        print("I Generated splits found alongside --auto_input_dataset, using them.")

    return train_set_path, dev_set_path, test_set_path, generated_alphabet_path
