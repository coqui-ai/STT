#!/usr/bin/env python
import argparse
import fnmatch
import multiprocessing
import os
import subprocess
import sys
import tarfile
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple, Optional

import pandas
from coqui_stt_training.util.downloader import maybe_download
from sox import Transformer
from tensorflow.python.platform import gfile
from tqdm import tqdm


@dataclass(frozen=True)
class LibriSpeechSetSpecs:
    url: str
    filename: str
    name: str
    csv: str


def set_specs_from_url(url: str) -> Tuple[str, LibriSpeechSetSpecs]:
    filename = os.path.basename(url)
    name = filename.replace(".tar.gz", "")
    csv = f"librivox-{name}.csv"
    return name, LibriSpeechSetSpecs(url, filename, name, csv)


def _download_and_preprocess_data(
    data_dir: Path, sets_to_process, sample_rate: int, relative: bool
):
    # Conditionally download data to data_dir
    print(
        f"Downloading Librivox data set (55GB) into {data_dir} if not already present..."
    )

    for spec in tqdm(sets_to_process):
        print(f"Downloading set {spec.name}...")
        archive_path = maybe_download(spec.filename, data_dir, spec.url)

        # Conditionally extract LibriSpeech data
        # We extract each archive into data_dir, but test for existence in
        # data_dir/LibriSpeech because the archives share that root.
        print(f"Extracting set {spec.name}...")
        extracted_dir = data_dir / "LibriSpeech" / spec.name
        if not extracted_dir.exists():
            _extract(archive=archive_path, dest_path=data_dir)

        # Convert FLAC data to wav, from:
        #  data_dir/LibriSpeech/split/1/2/1-2-3.flac
        # to:
        #  data_dir/LibriSpeech/split-wav/1/2/1-2-3.wav
        #
        # And process transcripts from **/*.trans.txt files
        print(
            f"Converting set {spec.name} from FLAC to WAV and processing transcripts..."
        )
        dataframe = _convert_audio_and_split_sentences(
            source_dir=extracted_dir,
            dest_dir=extracted_dir.parent / (extracted_dir.stem + "-wav"),
            sample_rate=sample_rate,
            relative_to=extracted_dir.parent if relative else None,
        )

        csv_path = data_dir / "LibriSpeech" / spec.csv
        print(f"Writing CSV to {csv_path}...")
        dataframe.to_csv(csv_path, index=False)


def _extract(archive, dest_path):
    tar = tarfile.open(archive)
    tar.extractall(dest_path)
    tar.close()


def _convert_single_flac(job):
    flac_file, wav_file, sample_rate = job
    tfm = Transformer()
    tfm.set_output_format(rate=sample_rate)
    tfm.build(str(flac_file), str(wav_file))
    return os.path.getsize(wav_file)


def _convert_audio_and_split_sentences(
    source_dir: Path, dest_dir: Path, sample_rate: int, relative_to: Optional[Path]
):
    os.makedirs(dest_dir, exist_ok=True)

    # Loop over transcription files and collect transcripts
    #
    # The format for each file 1-2.trans.txt is:
    #  1-2-0 transcription of 1-2-0.flac
    #  1-2-1 transcription of 1-2-1.flac
    #  ...
    #
    # We also convert the corresponding FLACs to WAV in the same pass
    files = []
    transcripts = []
    conversions = []
    wav_filesizes = []
    print("Collecting transcripts...")
    for trans_filename in tqdm(list(source_dir.rglob("*.trans.txt"))):
        with open(trans_filename, "r", encoding="utf-8") as fin:
            for line in fin:
                # Parse each segment line
                seqid, transcript = line.split(" ", maxsplit=1)

                # This is converting characters with diacritics to their base
                # versions without diacritics, and removing any non-ASCII characters
                # that survive this step.
                transcript = (
                    unicodedata.normalize("NFKD", transcript)
                    .encode("ascii", "ignore")
                    .decode("ascii", "ignore")
                )

                transcript = transcript.lower().strip()

                # Convert corresponding FLAC to a WAV
                base = trans_filename.parent.joinpath(seqid)
                flac_file = base.with_suffix(".flac")
                wav_file = (
                    dest_dir.joinpath(*seqid.split("-"))
                    .joinpath(seqid)
                    .with_suffix(".wav")
                )
                wav_file.parent.mkdir(parents=True, exist_ok=True)

                if wav_file.exists():
                    wav_filesizes.append(os.path.getsize(wav_file))
                else:
                    conversions.append((flac_file, wav_file, sample_rate))

                if relative_to:
                    wav_file = wav_file.relative_to(relative_to)

                files.append(str(wav_file))
                transcripts.append(transcript)

    if conversions:
        print(f"Converting {len(conversions)} FLAC files to WAV...")
        with multiprocessing.Pool() as pool:
            wav_filesizes = list(pool.map(_convert_single_flac, conversions))

    return pandas.DataFrame(
        data=zip(files, wav_filesizes, transcripts),
        columns=["wav_filename", "wav_filesize", "transcript"],
    )


def main():
    all_sets: Dict[str, LibriSpeechSetSpecs] = {
        name: specs
        for name, specs in [
            set_specs_from_url(url)
            for url in [
                "http://www.openslr.org/resources/12/train-clean-100.tar.gz",
                "http://www.openslr.org/resources/12/train-clean-360.tar.gz",
                "http://www.openslr.org/resources/12/train-other-500.tar.gz",
                "http://www.openslr.org/resources/12/dev-clean.tar.gz",
                "http://www.openslr.org/resources/12/dev-other.tar.gz",
                "http://www.openslr.org/resources/12/test-clean.tar.gz",
                "http://www.openslr.org/resources/12/test-other.tar.gz",
            ]
        ]
    }
    set_names = tuple(all_sets.keys())

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "base_folder",
        help="base folder where archives will be found or downloaded, and then processed",
    )
    parser.add_argument(
        "--sets",
        nargs="+",
        choices=set_names,
        help=f"which sets to download/process. space separated list. defaults to every set",
    )
    parser.add_argument(
        "--sample_rate",
        type=int,
        default=16000,
        help="sample rate to convert samples to",
    )
    parser.add_argument(
        "--relative",
        action="store_true",
        help="whether to store relative paths in CSV",
    )
    args = parser.parse_args()

    set_specs = [all_sets[set] for set in args.sets]
    _download_and_preprocess_data(
        Path(args.base_folder), set_specs, args.sample_rate, args.relative
    )


if __name__ == "__main__":
    main()
