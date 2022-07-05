#!/usr/bin/env python3
import csv
import os
import re
import subprocess
import random
import progressbar
import sox

from multiprocessing import Pool
from pathlib import Path

try:
    import zipfile38 as zipfile
except ImportError:
    print("ERROR: This importer needs additional dependencies. To fix run:")
    print("   python -m pip install zipfile38")
    raise

from coqui_stt_training.util.downloader import SIMPLE_BAR, maybe_download
from coqui_stt_training.util.importers import (
    get_counter,
    get_imported_samples,
    get_importers_parser,
    get_validate_label,
    print_import_report,
)

FIELDNAMES = ["wav_filename", "wav_filesize", "transcript"]
SAMPLE_RATE = 16000
MAX_SECS = 15
ARCHIVE_NAME = "2019-04-11_fr_FR"
ARCHIVE_DIR_NAME = "ts_" + ARCHIVE_NAME
ARCHIVE_URL = "https://drive.infomaniak.com/app/share/327683/85ec2469-8a64-4a8a-8de0-43e262d32d38/16/download"


def _download_and_preprocess_data(target_dir, english_compatible=False):
    # Making path absolute
    target_dir = os.path.abspath(target_dir)
    # Conditionally download data
    archive_path = maybe_download(
        "ts_" + ARCHIVE_NAME + ".zip", target_dir, ARCHIVE_URL
    )
    # Conditionally extract archive data
    _maybe_extract(target_dir, ARCHIVE_DIR_NAME, archive_path)
    # Conditionally convert TrainingSpeech data to DeepSpeech CSVs and wav
    _maybe_convert_sets(
        target_dir, ARCHIVE_DIR_NAME, english_compatible=english_compatible
    )


def _maybe_extract(target_dir, extracted_data, archive_path):
    # If target_dir/extracted_data does not exist, extract archive in target_dir
    extracted_path = os.path.join(target_dir, extracted_data)
    if not os.path.exists(extracted_path):
        print('No directory "%s" - extracting archive...' % extracted_path)
        if not os.path.isdir(extracted_path):
            os.mkdir(extracted_path)
        with zipfile.ZipFile(archive_path) as zip_f:
            zip_f.extractall(extracted_path)
    else:
        print('Found directory "%s" - not extracting it from archive.' % archive_path)


def one_sample(sample):
    """Take an audio file, and optionally convert it to 16kHz WAV"""
    orig_filename = sample["path"]
    # Storing wav files next to the wav ones - just with a different suffix
    wav_filename = os.path.splitext(orig_filename)[0] + ".converted.wav"
    _maybe_convert_wav(orig_filename, wav_filename)
    file_size = -1
    frames = 0
    duration = 0
    if os.path.exists(wav_filename):
        file_size = os.path.getsize(wav_filename)
        file_info = sox.file_info.info(wav_filename)
        frames = int(file_info.get("num_samples", frames))
        duration = int(file_info.get("duration", duration))
    label = sample["text"]

    rows = []

    # Keep track of how many samples are good vs. problematic
    counter = get_counter()
    if file_size == -1:
        # Excluding samples that failed upon conversion
        counter["failed"] += 1
    elif label is None:
        # Excluding samples that failed on label validation
        counter["invalid_label"] += 1
    elif int(duration * 1000 / 10 / 2) < len(str(label)):
        # Excluding samples that are too short to fit the transcript
        counter["too_short"] += 1
    elif duration > MAX_SECS:
        # Excluding very long samples to keep a reasonable batch-size
        counter["too_long"] += 1
    else:
        # This one is good - keep it for the target CSV
        rows.append((wav_filename, file_size, label))
        counter["imported_time"] += frames
    counter["all"] += 1
    counter["total_time"] += frames

    return (counter, rows)


def _maybe_convert_sets(target_dir, extracted_data, english_compatible=False):
    extracted_dir = os.path.join(target_dir, extracted_data)
    # override existing CSV with normalized one
    target_csv_template = os.path.join(target_dir, "ts_" + ARCHIVE_NAME + "_{}.csv")
    if os.path.isfile(target_csv_template):
        return
    path_to_original_csv = os.path.join(extracted_dir, "data.csv")
    with open(path_to_original_csv) as csv_f:
        data = [
            d
            for d in csv.DictReader(csv_f, delimiter=",")
            if float(d["duration"]) <= MAX_SECS
        ]

    for line in data:
        line["path"] = os.path.join(extracted_dir, line["path"])

    num_samples = len(data)
    rows = []
    counter = get_counter()

    print("Importing {} wav files...".format(num_samples))
    pool = Pool()
    bar = progressbar.ProgressBar(max_value=num_samples, widgets=SIMPLE_BAR)
    for i, processed in enumerate(pool.imap_unordered(one_sample, data), start=1):
        counter += processed[0]
        rows += processed[1]
        bar.update(i)
    bar.update(num_samples)
    pool.close()
    pool.join()

    with open(
        target_csv_template.format("train"), "w", encoding="utf-8", newline=""
    ) as train_csv_file, open(
        target_csv_template.format("dev"), "w", encoding="utf-8", newline=""
    ) as dev_csv_file, open(
        target_csv_template.format("test"), "w", encoding="utf-8", newline=""
    ) as test_csv_file:
        train_writer = csv.DictWriter(train_csv_file, fieldnames=FIELDNAMES)
        train_writer.writeheader()
        dev_writer = csv.DictWriter(dev_csv_file, fieldnames=FIELDNAMES)
        dev_writer.writeheader()
        test_writer = csv.DictWriter(test_csv_file, fieldnames=FIELDNAMES)
        test_writer.writeheader()

        train_set, dev_set, test_set = _split_sets(rows)

        # save train_set
        for item in train_set:
            transcript = validate_label(
                cleanup_transcript(item[2], english_compatible=english_compatible)
            )
            if not transcript:
                continue
            wav_filename = item[0]
            train_writer.writerow(
                dict(
                    wav_filename=Path(wav_filename).relative_to(target_dir),
                    wav_filesize=os.path.getsize(wav_filename),
                    transcript=transcript,
                )
            )

        # save dev_set
        for item in dev_set:
            transcript = validate_label(
                cleanup_transcript(item[2], english_compatible=english_compatible)
            )
            if not transcript:
                continue
            wav_filename = item[0]
            dev_writer.writerow(
                dict(
                    wav_filename=Path(wav_filename).relative_to(target_dir),
                    wav_filesize=os.path.getsize(wav_filename),
                    transcript=transcript,
                )
            )

        # save test_set
        for item in test_set:
            transcript = validate_label(
                cleanup_transcript(item[2], english_compatible=english_compatible)
            )
            if not transcript:
                continue
            wav_filename = item[0]
            test_writer.writerow(
                dict(
                    wav_filename=Path(wav_filename).relative_to(target_dir),
                    wav_filesize=os.path.getsize(wav_filename),
                    transcript=transcript,
                )
            )

    imported_samples = get_imported_samples(counter)
    assert counter["all"] == num_samples
    assert len(rows) == imported_samples

    print_import_report(counter, SAMPLE_RATE, MAX_SECS)


def _split_sets(rows):
    """
    randomply split the datasets into train, validation, and test sets where the size of the
    validation and test sets are determined by the `get_sample_size` function.
    """
    random.shuffle(rows)
    sample_size = get_sample_size(len(rows))

    train_beg = 0
    train_end = len(rows) - 2 * sample_size

    dev_beg = train_end
    dev_end = train_end + sample_size

    test_beg = dev_end
    test_end = len(rows)

    return (
        rows[train_beg:train_end],
        rows[dev_beg:dev_end],
        rows[test_beg:test_end],
    )


def get_sample_size(population_size):
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


def _maybe_convert_wav(orig_filename, wav_filename):
    if not os.path.exists(wav_filename):
        transformer = sox.Transformer()
        transformer.convert(samplerate=SAMPLE_RATE)
        try:
            transformer.build(orig_filename, wav_filename)
        except sox.core.SoxError as ex:
            print("SoX processing error", ex, orig_filename, wav_filename)


PUNCTUATIONS_REG = re.compile(r"[°\-,;!?.()\[\]*…—]")
MULTIPLE_SPACES_REG = re.compile(r"\s{2,}")


def cleanup_transcript(text, english_compatible=False):
    text = text.replace("’", "'").replace("\u00A0", " ")
    text = PUNCTUATIONS_REG.sub(" ", text)
    text = MULTIPLE_SPACES_REG.sub(" ", text)
    if english_compatible:
        text = str(text.encode("utf8", "ignore").decode("utf8", "ignore"))
    return text.strip().lower()


def handle_args():
    parser = get_importers_parser(
        description="Importer for TrainingSpeech dataset. More info at https://github.com/wasertech/TrainingSpeech."
    )
    parser.add_argument(dest="target_dir")
    parser.add_argument(
        "--english-compatible",
        action="store_true",
        dest="english_compatible",
        help="Remove diactrics and other non-ascii chars.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    cli_args = handle_args()
    validate_label = get_validate_label(cli_args)
    _download_and_preprocess_data(cli_args.target_dir, cli_args.english_compatible)
