#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This script is structured in a weird way, with delayed imports. This is due
# to the use of multiprocessing. TensorFlow cannot handle forking, and even with
# the spawn strategy set to "spawn" it still leads to weird problems, so we
# restructure the code so that TensorFlow is only imported inside the child
# processes.

import os
import sys
import glob
import itertools
import json
import multiprocessing
from multiprocessing import Pool, cpu_count
from dataclasses import dataclass, field

from coqui_stt_ctcdecoder import Scorer, ctc_beam_search_decoder_batch
from tqdm import tqdm


def fail(message, code=1):
    print(f"E {message}")
    sys.exit(code)


def transcribe_file(audio_path, tlog_path):
    log_level_index = (
        sys.argv.index("--log_level") + 1 if "--log_level" in sys.argv else 0
    )
    desired_log_level = (
        sys.argv[log_level_index] if 0 < log_level_index < len(sys.argv) else "3"
    )
    os.environ["TF_CPP_MIN_LOG_LEVEL"] = desired_log_level

    import tensorflow as tf
    import tensorflow.compat.v1 as tfv1

    from coqui_stt_training.train import create_model
    from coqui_stt_training.util.audio import AudioFile
    from coqui_stt_training.util.checkpoints import load_graph_for_evaluation
    from coqui_stt_training.util.config import Config
    from coqui_stt_training.util.feeding import split_audio_file

    initialize_transcribe_config()

    scorer = None
    if Config.scorer_path:
        scorer = Scorer(
            Config.lm_alpha, Config.lm_beta, Config.scorer_path, Config.alphabet
        )

    try:
        num_processes = cpu_count()
    except NotImplementedError:
        num_processes = 1

    with AudioFile(audio_path, as_path=True) as wav_path:
        data_set = split_audio_file(
            wav_path,
            batch_size=Config.batch_size,
            aggressiveness=Config.vad_aggressiveness,
            outlier_duration_ms=Config.outlier_duration_ms,
            outlier_batch_size=Config.outlier_batch_size,
        )
        iterator = tfv1.data.make_one_shot_iterator(data_set)
        batch_time_start, batch_time_end, batch_x, batch_x_len = iterator.get_next()
        no_dropout = [None] * 6
        logits, _ = create_model(
            batch_x=batch_x, seq_length=batch_x_len, dropout=no_dropout
        )
        transposed = tf.nn.softmax(tf.transpose(logits, [1, 0, 2]))
        tf.train.get_or_create_global_step()
        with tf.Session(config=Config.session_config) as session:
            load_graph_for_evaluation(session)
            transcripts = []
            while True:
                try:
                    starts, ends, batch_logits, batch_lengths = session.run(
                        [batch_time_start, batch_time_end, transposed, batch_x_len]
                    )
                except tf.errors.OutOfRangeError:
                    break
                decoded = ctc_beam_search_decoder_batch(
                    batch_logits,
                    batch_lengths,
                    Config.alphabet,
                    Config.beam_width,
                    num_processes=num_processes,
                    scorer=scorer,
                )
                decoded = list(d[0][1] for d in decoded)
                transcripts.extend(zip(starts, ends, decoded))
            transcripts.sort(key=lambda t: t[0])
            transcripts = [
                {"start": int(start), "end": int(end), "transcript": transcript}
                for start, end, transcript in transcripts
            ]
            with open(tlog_path, "w") as tlog_file:
                json.dump(transcripts, tlog_file, default=float)


def step_function(job):
    """ Wrap transcribe_file to unpack arguments from a single tuple """
    idx, src, dst = job
    transcribe_file(src, dst)
    return idx, src, dst


def transcribe_many(src_paths, dst_paths):
    from coqui_stt_training.util.config import Config, log_progress

    pool = Pool(processes=min(cpu_count(), len(src_paths)))

    # Create list of items to be processed: [(i, src_path[i], dst_paths[i])]
    jobs = zip(itertools.count(), src_paths, dst_paths)

    process_iterable = tqdm(
        pool.imap_unordered(step_function, jobs),
        desc="Transcribing files",
        total=len(src_paths),
        disable=not Config.show_progressbar,
    )

    for result in process_iterable:
        idx, src, dst = result
        log_progress(
            f'Transcribed file {idx+1} of {len(src_paths)} from "{src}" to "{dst}"'
        )


def transcribe_one(src_path, dst_path):
    transcribe_file(src_path, dst_path)
    print(f'I Transcribed file "{src_path}" to "{dst_path}"')


def resolve(base_path, spec_path):
    if spec_path is None:
        return None
    if not os.path.isabs(spec_path):
        spec_path = os.path.join(base_path, spec_path)
    return spec_path


def transcribe():
    from coqui_stt_training.util.config import Config

    initialize_transcribe_config()

    if not Config.src or not os.path.exists(Config.src):
        # path not given or non-existant
        fail(
            "You have to specify which file or catalog to transcribe via the --src flag."
        )
    else:
        # path given and exists
        src_path = os.path.abspath(Config.src)
        if os.path.isfile(src_path):
            if src_path.endswith(".catalog"):
                # Transcribe batch of files via ".catalog" file (from DSAlign)
                catalog_dir = os.path.dirname(src_path)
                with open(src_path, "r") as catalog_file:
                    catalog_entries = json.load(catalog_file)
                catalog_entries = [
                    (resolve(catalog_dir, e["audio"]), resolve(catalog_dir, e["tlog"]))
                    for e in catalog_entries
                ]
                if any(map(lambda e: not os.path.isfile(e[0]), catalog_entries)):
                    fail("Missing source file(s) in catalog")
                if not Config.force and any(
                    map(lambda e: os.path.isfile(e[1]), catalog_entries)
                ):
                    fail(
                        "Destination file(s) from catalog already existing, use --force for overwriting"
                    )
                if any(
                    map(
                        lambda e: not os.path.isdir(os.path.dirname(e[1])),
                        catalog_entries,
                    )
                ):
                    fail("Missing destination directory for at least one catalog entry")
                src_paths, dst_paths = zip(*paths)
                transcribe_many(src_paths, dst_paths)
            else:
                # Transcribe one file
                dst_path = (
                    os.path.abspath(Config.dst)
                    if Config.dst
                    else os.path.splitext(src_path)[0] + ".tlog"
                )
                if os.path.isfile(dst_path):
                    if Config.force:
                        transcribe_one(src_path, dst_path)
                    else:
                        fail(
                            'Destination file "{}" already existing - use --force for overwriting'.format(
                                dst_path
                            ),
                            code=0,
                        )
                elif os.path.isdir(os.path.dirname(dst_path)):
                    transcribe_one(src_path, dst_path)
                else:
                    fail("Missing destination directory")
        elif os.path.isdir(src_path):
            # Transcribe all files in dir
            print("Transcribing all WAV files in --src")
            if Config.recursive:
                wav_paths = glob.glob(os.path.join(src_path, "**", "*.wav"))
            else:
                wav_paths = glob.glob(os.path.join(src_path, "*.wav"))
            dst_paths = [path.replace(".wav", ".tlog") for path in wav_paths]
            transcribe_many(wav_paths, dst_paths)


def initialize_transcribe_config():
    from coqui_stt_training.util.config import (
        BaseSttConfig,
        initialize_globals_from_instance,
    )

    @dataclass
    class TranscribeConfig(BaseSttConfig):
        src: str = field(
            default="",
            metadata=dict(
                help="Source path to an audio file or directory or catalog file. "
                "Catalog files should be formatted from DSAlign. A directory "
                "will be recursively searched for audio. If --dst not set, "
                "transcription logs (.tlog) will be written in-place using the "
                'source filenames with suffix ".tlog" instead of ".wav".'
            ),
        )

        dst: str = field(
            default="",
            metadata=dict(
                help="path for writing the transcription log or logs (.tlog). "
                "If --src is a directory, this one also has to be a directory "
                "and the required sub-dir tree of --src will get replicated."
            ),
        )

        recursive: bool = field(
            default=False,
            metadata=dict(help="scan source directory recursively for audio"),
        )

        force: bool = field(
            default=False,
            metadata=dict(
                help="Forces re-transcribing and overwriting of already existing "
                "transcription logs (.tlog)"
            ),
        )

        vad_aggressiveness: int = field(
            default=3,
            metadata=dict(help="VAD aggressiveness setting (0=lowest, 3=highest)"),
        )

        batch_size: int = field(
            default=40,
            metadata=dict(help="Default batch size"),
        )

        outlier_duration_ms: int = field(
            default=10000,
            metadata=dict(
                help="Duration in ms after which samples are considered outliers"
            ),
        )

        outlier_batch_size: int = field(
            default=1,
            metadata=dict(help="Batch size for duration outliers (defaults to 1)"),
        )

        def __post_init__(self):
            if os.path.isfile(self.src) and self.src.endswith(".catalog") and self.dst:
                raise RuntimeError(
                    "Parameter --dst not supported if --src points to a catalog"
                )

            if os.path.isdir(self.src):
                if self.dst:
                    raise RuntimeError(
                        "Destination path not supported for batch decoding jobs."
                    )

            super().__post_init__()

    config = TranscribeConfig.init_from_argparse(arg_prefix="")
    initialize_globals_from_instance(config)


def main():
    from coqui_stt_training.util.helpers import check_ctcdecoder_version

    try:
        import webrtcvad
    except ImportError:
        print(
            "E transcribe module requires webrtcvad, which cannot be imported. Install with pip install webrtcvad"
        )
        sys.exit(1)

    check_ctcdecoder_version()
    transcribe()


if __name__ == "__main__":
    main()
