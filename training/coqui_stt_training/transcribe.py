#!/usr/bin/env python
# -*- coding: utf-8 -*-
import glob
import itertools
import json
import multiprocessing
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Tuple

LOG_LEVEL_INDEX = sys.argv.index("--log_level") + 1 if "--log_level" in sys.argv else 0
DESIRED_LOG_LEVEL = (
    sys.argv[LOG_LEVEL_INDEX] if 0 < LOG_LEVEL_INDEX < len(sys.argv) else "3"
)
os.environ["TF_CPP_MIN_LOG_LEVEL"] = DESIRED_LOG_LEVEL
import tensorflow as tf
import tensorflow.compat.v1 as tfv1

from coqui_stt_ctcdecoder import Scorer, ctc_beam_search_decoder_batch
from coqui_stt_training.train import create_model
from coqui_stt_training.util.audio import AudioFile
from coqui_stt_training.util.checkpoints import load_graph_for_evaluation
from coqui_stt_training.util.config import (
    BaseSttConfig,
    Config,
    initialize_globals_from_instance,
)
from coqui_stt_training.util.feeding import split_audio_file
from coqui_stt_training.util.helpers import check_ctcdecoder_version
from coqui_stt_training.util.multiprocessing import PoolBase
from tqdm import tqdm


def cpu_count():
    return os.cpu_count() or 1


class TranscriptionPool(PoolBase):
    def init(self):
        initialize_transcribe_config()

        self.scorer = None
        if Config.scorer_path:
            self.scorer = Scorer(
                Config.lm_alpha, Config.lm_beta, Config.scorer_path, Config.alphabet
            )

        # If we have GPUs available, scope the graph so that we only use one
        # GPU per child process. In this case, the pool should also be created
        # with only one process per GPU.
        if tf.test.is_gpu_available():
            with tf.device(f"/GPU:{self.process_id}"):
                self.create_graph()
        else:
            self.create_graph()

    def create_graph(self):
        self.batch_x_ph = tf.placeholder(tf.float32, [None, None, Config.n_input])
        self.batch_x_len_ph = tf.placeholder(tf.int32)

        no_dropout = [None] * 6
        logits, _ = create_model(
            batch_x=self.batch_x_ph,
            seq_length=self.batch_x_len_ph,
            dropout=no_dropout,
        )
        self.transposed = tf.nn.softmax(tf.transpose(logits, [1, 0, 2]))
        tfv1.train.get_or_create_global_step()

        self.session = tfv1.Session(config=Config.session_config)

        # Load checkpoint in a mutex way to avoid hangs in TensorFlow code
        with self.lock:
            load_graph_for_evaluation(self.session, silent=True)

    def run(self, job):
        idx, src, dst = job
        self.transcribe_file(src, dst)
        return idx, src, dst

    def transcribe_file(self, audio_path: Path, tlog_path: Path):
        with AudioFile(str(audio_path), as_path=True) as wav_path:
            data_set = split_audio_file(
                wav_path,
                batch_size=Config.batch_size,
                aggressiveness=Config.vad_aggressiveness,
                outlier_duration_ms=Config.outlier_duration_ms,
                outlier_batch_size=Config.outlier_batch_size,
            )
            iterator = tfv1.data.make_one_shot_iterator(data_set)
            (
                batch_time_start,
                batch_time_end,
                batch_x,
                batch_x_len,
            ) = iterator.get_next()

            transcripts = []
            while True:
                try:
                    starts, ends, batch_inputs, batch_lengths = self.session.run(
                        [batch_time_start, batch_time_end, batch_x, batch_x_len],
                    )

                    batch_logits = self.session.run(
                        self.transposed,
                        feed_dict={
                            self.batch_x_ph: batch_inputs,
                            self.batch_x_len_ph: batch_lengths,
                        },
                    )
                except tf.errors.OutOfRangeError:
                    break

                decoded = ctc_beam_search_decoder_batch(
                    batch_logits,
                    batch_lengths,
                    Config.alphabet,
                    Config.beam_width,
                    num_processes=cpu_count(),
                    scorer=self.scorer,
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


def transcribe_many(src_paths, dst_paths, mpctx=multiprocessing):
    # Create list of items to be processed: [(i, src_path[i], dst_paths[i])]
    jobs = zip(itertools.count(), src_paths, dst_paths)

    if tf.test.is_gpu_available():
        num_gpus = len(tf.config.experimental.list_physical_devices("GPU"))
        num_processes = min(num_gpus, len(src_paths))
    else:
        num_processes = min(cpu_count(), len(src_paths))

    with TranscriptionPool.create(processes=num_processes, context=mpctx) as pool:
        process_iterable = tqdm(
            pool.imap_unordered(jobs),
            desc="Transcribing files",
            total=len(src_paths),
            disable=not Config.show_progressbar,
        )

        cwd = Path.cwd()
        for result in process_iterable:
            idx, src, dst = result
            # Revert to relative if possible to make logs more concise
            # if path is not relative to cwd, use the absolute path
            # (Path.is_relative_to is only available in Python >=3.9)
            try:
                src = src.relative_to(cwd)
            except ValueError:
                pass
            try:
                dst = dst.relative_to(cwd)
            except ValueError:
                pass
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
    src_paths = list(glob_method("*.wav"))
    dst_paths = [path.with_suffix(".tlog") for path in src_paths]
    return src_paths, dst_paths


def transcribe(mpctx=multiprocessing):
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

                transcribe_many([src_path], [dst_path], mpctx)
            else:
                # Transcribe from .catalog input
                src_paths, dst_paths = get_tasks_from_catalog(src_path)
                transcribe_many(src_paths, dst_paths, mpctx)
        elif src_path.is_dir():
            # Transcribe from dir input
            print(f"Transcribing all files in --src directory {src_path}")
            src_paths, dst_paths = get_tasks_from_dir(src_path, Config.recursive)
            transcribe_many(src_paths, dst_paths, mpctx)


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


def initialize_transcribe_config():
    config = TranscribeConfig.init_from_argparse(arg_prefix="")
    initialize_globals_from_instance(config)


def main():
    try:
        import webrtcvad
    except ImportError:
        print(
            "E transcribe module requires webrtcvad, which cannot be imported. Install with pip install webrtcvad"
        )
        sys.exit(1)

    check_ctcdecoder_version()
    # Set start method to spawn on all platforms to avoid issues with TensorFlow
    mpctx = multiprocessing.get_context("spawn")
    transcribe(mpctx)


if __name__ == "__main__":
    main()
