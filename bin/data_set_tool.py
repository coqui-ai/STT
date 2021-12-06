#!/usr/bin/env python
"""
Tool for building a combined SDB or CSV sample-set from other sets
Use 'python3 data_set_tool.py -h' for help
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import progressbar
from coqui_stt_training.util.audio import (
    AUDIO_TYPE_OPUS,
    AUDIO_TYPE_PCM,
    AUDIO_TYPE_WAV,
    change_audio_types,
)
from coqui_stt_training.util.augmentations import (
    SampleAugmentation,
    apply_sample_augmentations,
    parse_augmentations,
)
from coqui_stt_training.util.config import (
    BaseSttConfig,
    Config,
    initialize_globals_from_instance,
)
from coqui_stt_training.util.downloader import SIMPLE_BAR
from coqui_stt_training.util.sample_collections import (
    CSVWriter,
    DirectSDBWriter,
    TarWriter,
    samples_from_sources,
)

AUDIO_TYPE_LOOKUP = {"wav": AUDIO_TYPE_WAV, "opus": AUDIO_TYPE_OPUS}


def build_data_set():
    audio_type = AUDIO_TYPE_LOOKUP[Config.audio_type]
    augmentations = parse_augmentations(Config.augment)
    print(f"Parsed augmentations from flags: {augmentations}")
    if any(not isinstance(a, SampleAugmentation) for a in augmentations):
        print(
            "Warning: Some of the specified augmentations will not get applied, as this tool only supports "
            "overlay, codec, reverb, resample and volume."
        )
    extension = "".join(Path(Config.target).suffixes).lower()
    labeled = not Config.unlabeled
    if extension == ".csv":
        writer = CSVWriter(
            Config.target, absolute_paths=Config.absolute_paths, labeled=labeled
        )
    elif extension == ".sdb":
        writer = DirectSDBWriter(Config.target, audio_type=audio_type, labeled=labeled)
    elif extension == ".tar":
        writer = TarWriter(
            Config.target, labeled=labeled, gz=False, include=Config.include
        )
    elif extension in (".tgz", ".tar.gz"):
        writer = TarWriter(
            Config.target, labeled=labeled, gz=True, include=Config.include
        )
    else:
        raise RuntimeError(
            "Unknown extension of target file - has to be either .csv, .sdb, .tar, .tar.gz or .tgz"
        )
    with writer:
        samples = samples_from_sources(Config.sources, labeled=not Config.unlabeled)
        num_samples = len(samples)
        if augmentations:
            samples = apply_sample_augmentations(
                samples, audio_type=AUDIO_TYPE_PCM, augmentations=augmentations
            )
        bar = progressbar.ProgressBar(max_value=num_samples, widgets=SIMPLE_BAR)
        for sample in bar(
            change_audio_types(
                samples,
                audio_type=audio_type,
                bitrate=Config.bitrate,
                processes=Config.workers,
            )
        ):
            writer.add(sample)


@dataclass
class DatasetToolConfig(BaseSttConfig):
    sources: List[str] = field(
        default_factory=list,
        metadata=dict(
            help="Source CSV and/or SDB files - "
            "Note: For getting a correctly ordered target set, source SDBs have to have their samples "
            "already ordered from shortest to longest.",
        ),
    )
    target: str = field(
        default="",
        metadata=dict(
            help="SDB, CSV or TAR(.gz) file to create",
        ),
    )
    audio_type: str = field(
        default="opus",
        metadata=dict(
            help="Audio representation inside target SDB",
        ),
    )
    bitrate: int = field(
        default=16000,
        metadata=dict(
            help="Bitrate for lossy compressed SDB samples like in case of --audio-type opus",
        ),
    )
    workers: Optional[int] = field(
        default=None,
        metadata=dict(
            help="Number of encoding SDB workers",
        ),
    )
    unlabeled: bool = field(
        default=False,
        metadata=dict(
            help="If to build an data-set with unlabeled (audio only) samples - "
            "typically used for building noise augmentation corpora",
        ),
    )
    absolute_paths: bool = field(
        default=False,
        metadata=dict(
            help="If to reference samples by their absolute paths when writing CSV files",
        ),
    )
    include: List[str] = field(
        default_factory=list,
        metadata=dict(
            help="Adds files to the root directory of .tar(.gz) targets",
        ),
    )

    def __post_init__(self):
        if self.audio_type not in AUDIO_TYPE_LOOKUP.keys():
            raise RuntimeError(
                f"--audio_type must be one of {tuple(AUDIO_TYPE_LOOKUP.keys())}"
            )

        if not self.sources:
            raise RuntimeError("No source specified with --sources")

        if not self.target:
            raise RuntimeError("No target specified with --target")


def main():
    config = DatasetToolConfig.init_from_argparse(arg_prefix="")
    initialize_globals_from_instance(config)

    build_data_set()


if __name__ == "__main__":
    main()
