#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This script is structured in a weird way, with delayed imports. This is due
# to the use of multiprocessing. TensorFlow cannot handle forking, and even with
# the spawn strategy set to "spawn" it still leads to weird problems, so we
# restructure the code so that TensorFlow is only imported inside the child
# processes.

import glob
import itertools
import json
import multiprocessing
import os
import sys
from dataclasses import dataclass, field
from multiprocessing import Pool, Lock, cpu_count
from pathlib import Path
from typing import Optional, List, Tuple

from coqui_stt_ctcdecoder import Scorer, ctc_beam_search_decoder_batch
from tqdm import tqdm


def transcribe_file(audio_path: Path, tlog_path: Path):
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

    with AudioFile(str(audio_path), as_path=True) as wav_path:
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
            # Load checkpoint in a mutex way to avoid hangs in TensorFlow code
            with lock:
                load_graph_for_evaluation(session, silent=True)
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


def init_fn(l):
    global lock
    lock = l


def step_function(job):
    """Wrap transcribe_file to unpack arguments from a single tuple"""
    idx, src, dst = job
    transcribe_file(src, dst)
    return idx, src, dst


def transcribe_many(src_paths, dst_paths):
    from coqui_stt_training.util.config import Config, log_progress

    # Create list of items to be processed: [(i, src_path[i], dst_paths[i])]
    jobs = zip(itertools.count(), src_paths, dst_paths)

    lock = Lock()
    with Pool(
        processes=min(cpu_count(), len(src_paths)),
        initializer=init_fn,
        initargs=(lock,),
    ) as pool:
        process_iterable = tqdm(
            pool.imap_unordered(step_function, jobs),
            desc="Transcribing files",
            total=len(src_paths),
            disable=not Config.show_progressbar,
        )

        cwd = Path.cwd()
        for result in process_iterable:
            idx, src, dst = result
            # Revert to relative to avoid spamming logs
            if not src.is_absolute():
                src = src.relative_to(cwd)
            if not dst.is_absolute():
                dst = dst.relative_to(cwd)
            tqdm.write(f'[{idx+1}]: "{src}" -> "{dst}"')


def get_tasks_from_catalog(catalog_file_path: Path) -> Tuple[List[Path], List[Path]]:
    """Given a `catalog_file_path` pointing to a .catalog file (from DSAlign),
    extract transcription tasks, ie. (src_path, dest_path) pairs corresponding to
    a path to an audio file to be transcribed, and a path to a JSON file to place
    transcription results. For .catalog file inputs, these are taken from the
    "audio" and "tlog" properties of the entries in the catalog, with any relative
    paths being absolutized relative to the directory containing the .catalog file.
    """
    assert catalog_file_path.suffix == ".catalog"

    catalog_dir = catalog_file_path.parent
    with open(catalog_file_path, "r") as catalog_file:
        catalog_entries = json.load(catalog_file)

    def resolve(spec_path: Optional[Path]):
        if spec_path is None:
            return None
        if not spec_path.is_absolute():
            spec_path = catalog_dir / spec_path
        return spec_path

    catalog_entries = [
        (resolve(Path(e["audio"])), resolve(Path(e["tlog"]))) for e in catalog_entries
    ]

    for src, dst in catalog_entries:
        if not Config.force and dst.is_file():
            raise RuntimeError(
                f"Destination file already exists: {dst}. Use --force for overwriting."
            )

        if not dst.parent.is_dir():
            dst.parent.mkdir(parents=True)

    src_paths, dst_paths = zip(*catalog_entries)
    return src_paths, dst_paths


def get_tasks_from_dir(src_dir: Path, recursive: bool) -> Tuple[List[Path], List[Path]]:
    """Given a directory `src_dir` containing audio files, scan it for audio files
    and return transcription tasks, ie. (src_path, dest_path) pairs corresponding to
    a path to an audio file to be transcribed, and a path to a JSON file to place
    transcription results.
    """
    glob_method = src_dir.rglob if recursive else src_dir.glob
    src_paths = list(itertools.chain(glob_method("*.wav"), glob_method("*.opus")))
    dst_paths = [path.with_suffix(".tlog") for path in src_paths]
    return src_paths, dst_paths


def transcribe():
    from coqui_stt_training.util.config import Config

    initialize_transcribe_config()

    src_path = Path(Config.src).resolve()
    if not Config.src or not src_path.exists():
        # path not given or non-existant
        raise RuntimeError(
            "You have to specify which audio file, catalog file or directory to "
            "transcribe with the --src flag."
        )
    else:
        # path given and exists
        if src_path.is_file():
            if src_path.suffix != ".catalog":
                # Transcribe one file
                dst_path = (
                    Path(Config.dst).resolve()
                    if Config.dst
                    else src_path.with_suffix(".tlog")
                )

                if dst_path.is_file() and not Config.force:
                    raise RuntimeError(
                        f'Destination file "{dst_path}" already exists - use '
                        "--force for overwriting."
                    )

                if not dst_path.parent.is_dir():
                    raise RuntimeError("Missing destination directory")

                transcribe_many([src_path], [dst_path])
            else:
                # Transcribe from .catalog input
                src_paths, dst_paths = get_tasks_from_catalog(src_path)
                transcribe_many(src_paths, dst_paths)
        elif src_path.is_dir():
            # Transcribe from dir input
            print(f"Transcribing all files in --src directory {src_path}")
            src_paths, dst_paths = get_tasks_from_dir(src_path, Config.recursive)
            transcribe_many(src_paths, dst_paths)


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
                'source filenames with suffix ".tlog" instead of the original.'
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

    # Set start method to spawn on all platforms to avoid issues with TensorFlow
    multiprocessing.set_start_method("spawn")

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
