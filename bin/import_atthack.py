#!/usr/bin/env python3
import csv
import os
import random
import subprocess
import tarfile
import unicodedata
from tqdm import tqdm

from glob import glob
from multiprocessing import Pool
from pathlib import Path

from coqui_stt_ctcdecoder import Alphabet
from coqui_stt_training.util.downloader import SIMPLE_BAR, maybe_download
from coqui_stt_training.util.importers import (
    get_counter,
    get_imported_samples,
    get_importers_parser,
    get_validate_label,
    print_import_report,
)

try:
    ffmpeg_path = (
        subprocess.check_output(["which", "ffmpeg"], stderr=subprocess.STDOUT)
        .decode()
        .replace("\n", "")
    )
    if not ffmpeg_path:
        raise subprocess.CalledProcessError
    else:
        print(f"Using FFMPEG from {str(ffmpeg_path)}.")
except subprocess.CalledProcessError:
    print("ERROR: This importer needs FFMPEG.")
    print()
    print("Type:")
    print("$ apt-get update && apt-get install -y --no-install-recommends ffmpeg")
    exit(1)

FIELDNAMES = ["wav_filename", "wav_filesize", "transcript"]
SAMPLE_RATE = 16000
CHANNELS = 1

ARCHIVE_DIR_NAME = "Att-HACK"
ARCHIVE_EXT = ".tgz"
ARCHIVE_NAME_txt = "txt"
ARCHIVE_NAME_wav = "wav"
BASE_SLR_URL = "http://www.openslr.org/resources/88"
ARCHIVE_URL_txt = f"{BASE_SLR_URL}/{ARCHIVE_NAME_txt}{ARCHIVE_EXT}"
ARCHIVE_URL_wav = f"{BASE_SLR_URL}/{ARCHIVE_NAME_wav}{ARCHIVE_EXT}"
ARCHIVE_ROOT_PATH = "Volumes/CLEM_HDD/IRCAM/Open_SLR"

_excluded_sentences = []


def _download_and_preprocess_data(target_dir):
    # Making path absolute
    target_dir = os.path.abspath(target_dir)
    # Conditionally download data
    txt_archive_path = maybe_download(
        f"{ARCHIVE_NAME_txt}{ARCHIVE_EXT}", target_dir, ARCHIVE_URL_txt
    )
    wav_archive_path = maybe_download(
        f"{ARCHIVE_NAME_wav}{ARCHIVE_EXT}", target_dir, ARCHIVE_URL_wav
    )
    # Conditionally extract data
    _maybe_extract(
        target_dir, f"{ARCHIVE_ROOT_PATH}/{ARCHIVE_NAME_txt}", txt_archive_path
    )
    _maybe_extract(
        target_dir, f"{ARCHIVE_ROOT_PATH}/{ARCHIVE_NAME_wav}", wav_archive_path
    )
    # Produce CSV files
    _maybe_convert_sets(target_dir, ARCHIVE_ROOT_PATH)

    if SAVE_EXCLUDED_MAX_SEC_TO_DISK:
        save_sentences_to_txt(_excluded_sentences, SAVE_EXCLUDED_MAX_SEC_TO_DISK)


def _maybe_extract(target_dir, extracted_data, archive_path):
    # If target_dir/extracted_data does not exist, extract archive in target_dir
    try:
        extracted_path = os.path.join(target_dir, extracted_data)
        if os.path.exists(extracted_path):
            print(
                'Found directory "%s" - not extracting it from archive.'
                % extracted_path
            )
        else:
            raise FileNotFoundError
    except FileNotFoundError:
        print('No directory "%s" - extracting archive...' % extracted_path)
        tar = tarfile.open(archive_path)
        tar.extractall(target_dir)
        tar.close()


def save_sentences_to_txt(sentences, text_file):
    with open(text_file, "w") as f:
        f.write("\n".join(sentences))


def one_sample(sample):
    """Take an audio file, and optionally convert it to 16kHz mono channel WAV"""
    wav_filename = sample[0]
    original_wav = wav_filename
    formatted_wav = os.path.splitext(wav_filename)[0] + "_.wav"
    _maybe_convert_wav(original_wav, formatted_wav)
    wav_filename = formatted_wav
    file_size = -1
    frames = 0
    if os.path.exists(wav_filename):
        file_size = os.path.getsize(wav_filename)
        frames = int(
            subprocess.check_output(
                ["soxi", "-s", wav_filename], stderr=subprocess.STDOUT
            )
        )
    label = label_filter(sample[1])
    counter = get_counter()
    rows = []
    if file_size == -1:
        # Excluding samples that failed upon conversion
        counter["failed"] += 1
    elif label is None:
        # Excluding samples that failed on label validation
        counter["invalid_label"] += 1
    elif int(frames / SAMPLE_RATE * 1000 / 15 / 2) < len(str(label)):
        # Excluding samples that are too short to fit the transcript
        counter["too_short"] += 1
    elif float(frames / SAMPLE_RATE) < MIN_SECS:
        # Excluding samples that are too short
        counter["too_short"] += 1
    elif float(frames / SAMPLE_RATE) > MAX_SECS:
        # Excluding very long samples to keep a reasonable batch-size
        counter["too_long"] += 1
        if SAVE_EXCLUDED_MAX_SEC_TO_DISK:
            _excluded_sentences.append(str(label))
    else:
        # This one is good - keep it for the target CSV
        rows.append((wav_filename, file_size, label))
        counter["imported_time"] += frames
    counter["all"] += 1
    counter["total_time"] += frames

    return (counter, rows)


def _maybe_convert_sets(target_dir, extracted_data):
    extracted_dir = os.path.join(target_dir, extracted_data)
    # override existing CSV with normalized one
    try:
        target_csv_template = os.path.join(
            target_dir, "".join([ARCHIVE_DIR_NAME, "_{}.csv"])
        )
        if os.path.isfile(target_csv_template):
            return
        else:
            raise FileNotFoundError
    except FileNotFoundError:

        all_files = glob(f"{extracted_dir}/{ARCHIVE_NAME_txt}/*.txt")

        transcripts = {}
        for tr in all_files:
            with open(tr, "r") as tr_source:
                transcript = tr_source.read()
                audio = os.path.basename(tr).replace(".txt", ".wav")
                transcripts[audio] = transcript
                tr_source.close()

        # Get audiofile path and transcript for each sentence
        samples = []
        for record in glob(f"{extracted_dir}/{ARCHIVE_NAME_wav}/*.wav"):
            record_file = os.path.basename(record)
            if record_file in transcripts.keys():
                samples.append((record, transcripts[record_file]))

        # Keep track of how many samples are good vs. problematic
        counter = get_counter()
        num_samples = len(samples)
        rows = []

        print("Importing WAV files...")
        pool = Pool()
        bar = tqdm(
            enumerate(pool.imap_unordered(one_sample, samples), start=1),
            total=num_samples,
        )
        for i, processed in bar:
            bar.set_description(
                f"Processing|{str(i)}/{str(num_samples)} ({int(i/num_samples*100)}%)"
            )
            counter += processed[0]
            rows += processed[1]
            bar.update(i)
        bar.update(num_samples)
        pool.close()
        pool.join()

        target_csv_template = os.path.join(
            target_dir, "".join([ARCHIVE_DIR_NAME, "_{}.csv"])
        )

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
                transcript = validate_label(item[2])
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
                transcript = validate_label(item[2])
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
                transcript = validate_label(item[2])
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


def _maybe_convert_wav(mp3_filename, wav_filename):
    if not os.path.exists(wav_filename):
        subprocess.check_call(
            [
                "ffmpeg",
                "-i",
                mp3_filename,
                "-acodec",
                "pcm_s16le",
                "-ac",
                str(CHANNELS),
                "-ar",
                str(SAMPLE_RATE),
                wav_filename,
            ]
        )


def handle_args():
    parser = get_importers_parser(
        description="Importer for Att-HACK French dataset. More information on http://www.openslr.org/88/."
    )
    parser.add_argument(dest="target_dir")
    parser.add_argument(
        "--filter_alphabet",
        help="Exclude samples with characters not in provided alphabet",
    )
    parser.add_argument(
        "--normalize",
        action="store_true",
        help="Converts diacritic characters to their base ones",
    )
    parser.add_argument(
        "--min_sec",
        type=float,
        help="[FLOAT] Min audio length in sec (default: 0.85)",
        default=0.85,
    )
    parser.add_argument(
        "--max_sec",
        type=float,
        help="[FLOAT] Max audio length in sec (default: 15.0)",
        default=10.0,
    )
    parser.add_argument(
        "--save_excluded_max_sec_to_disk",
        type=str,
        help="Text file path to save excluded (max length) sentences to add them to the language model",
    )
    return parser.parse_args()


if __name__ == "__main__":
    CLI_ARGS = handle_args()
    ALPHABET = Alphabet(CLI_ARGS.filter_alphabet) if CLI_ARGS.filter_alphabet else None

    MAX_SECS = CLI_ARGS.max_sec
    MIN_SECS = CLI_ARGS.min_sec

    SAVE_EXCLUDED_MAX_SEC_TO_DISK = CLI_ARGS.save_excluded_max_sec_to_disk

    validate_label = get_validate_label(CLI_ARGS)

    def label_filter(label):
        if CLI_ARGS.normalize:
            label = (
                unicodedata.normalize("NFKD", label.strip())
                .encode("ascii", "ignore")
                .decode("ascii", "ignore")
            )
        label = validate_label(label)
        if ALPHABET and label and not ALPHABET.CanEncode(label):
            label = None
        return label

    _download_and_preprocess_data(target_dir=CLI_ARGS.target_dir)
