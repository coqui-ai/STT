#!/usr/bin/env python
import argparse
import ctypes
import os
from pathlib import Path

import pandas
from tqdm import tqdm


def read_ogg_opus_duration(ogg_file_path):
    error = ctypes.c_int()
    opusfile = pyogg.opus.op_open_file(
        ogg_file_path.encode("utf-8"), ctypes.pointer(error)
    )

    if error.value != 0:
        raise ValueError(
            ("Ogg/Opus file could not be read." "Error code: {}").format(error.value)
        )

    pcm_buffer_size = pyogg.opus.op_pcm_total(opusfile, -1)
    channel_count = pyogg.opus.op_channel_count(opusfile, -1)
    sample_rate = 48000  # opus files are always 48kHz
    sample_width = 2  # always 16-bit
    pyogg.opus.op_free(opusfile)
    return pcm_buffer_size / sample_rate


def main(root_dir):
    for subset in (
        "train",
        "dev",
        "test",
    ):
        print("Processing {} subset...".format(subset))
        with open(Path(root_dir) / subset / "transcripts.txt") as fin:
            subset_entries = []
            for i, line in tqdm(enumerate(fin)):
                audio_id, transcript = line.split("\t")
                audio_id_parts = audio_id.split("_")
                # e.g. 4800_10003_000000 -> train/audio/4800/10003/4800_10003_000000.opus
                audio_path = (
                    Path(root_dir)
                    / subset
                    / "audio"
                    / audio_id_parts[0]
                    / audio_id_parts[1]
                    / "{}.opus".format(audio_id)
                )
                audio_duration = read_ogg_opus_duration(audio_path)
                # TODO: support other languages
                transcript = (
                    transcript.strip()
                    .replace("-", " ")
                    .replace("ñ", "n")
                    .replace(".", "")
                    .translate(
                        {
                            ord(ch): None
                            for ch in (
                                "а",
                                "в",
                                "е",
                                "и",
                                "к",
                                "м",
                                "н",
                                "о",
                                "п",
                                "р",
                                "т",
                                "ы",
                                "я",
                            )
                        }
                    )
                )
                subset_entries.append(
                    (
                        audio_path.relative_to(root_dir),
                        audio_duration,
                        transcript.strip(),
                    )
                )
            df = pandas.DataFrame(
                columns=["wav_filename", "wav_filesize", "transcript"],
                data=subset_entries,
            )
            csv_name = Path(root_dir) / "{}.csv".format(subset)
            df.to_csv(csv_name, index=False)
            print("Wrote {}".format(csv_name))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root_dir", help="Path to the mls_english_opus directory.")
    args = parser.parse_args()
    main(args.root_dir)
