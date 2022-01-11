#!/usr/bin/env python
import argparse
import ctypes
import os
import tarfile
import pandas
import pyogg

from pathlib import Path
from tqdm import tqdm
from coqui_stt_ctcdecoder import Alphabet
from coqui_stt_training.util.downloader import SIMPLE_BAR, maybe_download
from coqui_stt_training.util.importers import (
    get_counter,
    get_imported_samples,
    get_importers_parser,
    get_validate_label,
    print_import_report,
)

FIELDNAMES = ["wav_filename", "wav_filesize", "transcript"]
SAMPLE_RATE = 48000 # opus files are always 48kHz
SAMPLE_WIDTH = 2 # always 16-bit (2*8)
CHANNELS = 1
MAX_SECS = 10

LANGUAGE_LIST = [
    "english",
    "german",
    "french",
    "dutch",
    "spanish",
    "italian",
    "portuguese",
    "polish"
]

ARCHIVE_DIR_NAME = "MLS"
ARCHIVE_EXT = ".tar.gz"

BASE_SLR_URL = "https://dl.fbaipublicfiles.com/mls/"

class ValidateLangAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if values not in LANGUAGE_LIST:
            print("Got value:", values)
            raise ValueError(f"Choose from the availible languages: {str(LANGUAGE_LIST)}")
        setattr(namespace, self.dest, values)

def _download_and_preprocess_data(target_dir):
    # Making path absolute
    target_dir = os.path.abspath(target_dir)
    # Conditionally download data
    lm_archive_path = maybe_download(f"{ARCHIVE_NAME_LM}{ARCHIVE_EXT}", target_dir, ARCHIVE_URL_LM)
    asr_archive_path = maybe_download(f"{ARCHIVE_NAME_ASR}{ARCHIVE_EXT}", target_dir, ARCHIVE_URL_ASR)
    # Conditionally extract data
    _maybe_extract(target_dir, f"{ARCHIVE_NAME_LM}", lm_archive_path)
    _maybe_extract(target_dir, f"{ARCHIVE_NAME_ASR}", asr_archive_path)
    # Produce CSV files
    _maybe_convert_sets(target_dir, ARCHIVE_NAME_ASR)

def _maybe_extract(target_dir, extracted_data, archive_path):
    # If target_dir/extracted_data does not exist, extract archive in target_dir
    try:
        extracted_path = os.path.join(target_dir, extracted_data)
        if os.path.exists(extracted_path):
            print('Found directory "%s" - not extracting it from archive.' % extracted_path)
        else:
            raise FileNotFoundError
    except FileNotFoundError:
        print('No directory "%s" - extracting archive...' % extracted_path)
        tar = tarfile.open(archive_path)
        tar.extractall(target_dir)
        tar.close()

def read_ogg_opus_duration(ogg_file_path):
    error = ctypes.c_int()
    opusfile = pyogg.opus.op_open_file(
        ogg_file_path.as_posix().encode("utf-8"), ctypes.pointer(error)
    )

    if error.value != 0:
        raise ValueError(
            ("Ogg/Opus file {} could not be read." "Error code: {}").format(ogg_file_path.as_posix().encode("utf-8"), error.value)
        )

    pcm_buffer_size = pyogg.opus.op_pcm_total(opusfile, -1)
    channel_count = pyogg.opus.op_channel_count(opusfile, -1)
    sample_rate = SAMPLE_RATE
    sample_width = SAMPLE_WIDTH
    pyogg.opus.op_free(opusfile)
    return pcm_buffer_size / sample_rate


def _maybe_convert_sets(target_dir, extracted_data):
    extracted_dir = os.path.join(target_dir, extracted_data)
    for subset in (
        "train",
        "dev",
        "test",
    ):
        print("Processing {} subset...".format(subset))
        with open(Path(extracted_dir) / subset / "transcripts.txt") as fin:
            subset_entries = []
            for i, line in tqdm(enumerate(fin)):
                audio_id, transcript = line.split("\t")
                audio_id_parts = audio_id.split("_")
                # e.g. 4800_10003_000000 -> train/audio/4800/10003/4800_10003_000000.opus
                audio_path = (
                    Path(extracted_dir)
                    / subset
                    / "audio"
                    / audio_id_parts[0]
                    / audio_id_parts[1]
                    / "{}.opus".format(audio_id)
                )
                audio_duration = read_ogg_opus_duration(audio_path)
                transcript = label_filter(transcript)
                subset_entries.append(
                    (
                        audio_path.relative_to(extracted_dir),
                        audio_duration,
                        transcript.strip(),
                    )
                )
            df = pandas.DataFrame(
                columns=FIELDNAMES,
                data=subset_entries,
            )
            csv_name = Path(target_dir) / "{}.csv".format(subset)
            df.to_csv(csv_name, index=False)
            print("Wrote {}".format(csv_name))


def handle_args():
    parser = get_importers_parser(
        description="Importer for MLS dataset. More information on http://www.openslr.org/94/."
    )
    parser.add_argument(
        '-l',
        '--language',
        action=ValidateLangAction,
        help="Select language to download, process and import"
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
    return parser.parse_args()

if __name__ == "__main__":
    CLI_ARGS = handle_args()
    ALPHABET = Alphabet(CLI_ARGS.filter_alphabet) if CLI_ARGS.filter_alphabet else None
    LANGUAGE = CLI_ARGS.language
    ARCHIVE_NAME_LM = f"mls_lm_{LANGUAGE}"
    ARCHIVE_NAME_ASR = f"mls_{LANGUAGE}_opus"
    ARCHIVE_URL_LM = f"{BASE_SLR_URL}/{ARCHIVE_NAME_LM}{ARCHIVE_EXT}"
    ARCHIVE_URL_ASR = f"{BASE_SLR_URL}/{ARCHIVE_NAME_ASR}{ARCHIVE_EXT}"

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