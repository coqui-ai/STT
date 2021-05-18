#!/usr/bin/env python
"""
Tool for playing (and augmenting) single samples or samples from Sample Databases (SDB files) and 🐸STT CSV files
Use "python3 play.py -h" for help
"""

import argparse
import os
import random
import sys

from coqui_stt_training.util.audio import (
    AUDIO_TYPE_PCM,
    AUDIO_TYPE_WAV,
    get_loadable_audio_type_from_extension,
)
from coqui_stt_training.util.augmentations import (
    SampleAugmentation,
    apply_sample_augmentations,
    parse_augmentations,
)
from coqui_stt_training.util.sample_collections import (
    LabeledSample,
    SampleList,
    samples_from_source,
)


def get_samples_in_play_order():
    ext = os.path.splitext(Config.source)[1].lower()
    if get_loadable_audio_type_from_extension(ext):
        with open(Config.source, "rb") as fin:
            samples = [Sample(AUDIO_TYPE_WAV, fin.read(), sample_id=Config.source)]
    else:
        samples = samples_from_source(Config.source, buffering=0)
    played = 0
    index = Config.start
    while True:
        if 0 <= Config.number <= played:
            return
        if Config.random:
            yield samples[random.randint(0, len(samples) - 1)]
        elif index < 0:
            yield samples[len(samples) + index]
        elif index >= len(samples):
            raise RuntimeError("No sample with index {}".format(Config.start))
        else:
            yield samples[index]
        played += 1
        index = (index + 1) % len(samples)


def play_collection():
    if any(not isinstance(a, SampleAugmentation) for a in Config.augmentations):
        print("Warning: Some of the augmentations cannot be simulated by this command.")
    samples = get_samples_in_play_order()
    samples = apply_sample_augmentations(
        samples,
        audio_type=AUDIO_TYPE_PCM,
        augmentations=augmentations,
        process_ahead=0,
        clock=CLI_ARGS.clock,
    )
    for sample in samples:
        if not Config.quiet:
            print('Sample "{}"'.format(sample.sample_id), file=sys.stderr)
            if isinstance(sample, LabeledSample):
                print('  "{}"'.format(sample.transcript), file=sys.stderr)
        if Config.pipe:
            sample.change_audio_type(AUDIO_TYPE_WAV)
            sys.stdout.buffer.write(sample.audio.getvalue())
            return
        wave_obj = simpleaudio.WaveObject(
            sample.audio,
            sample.audio_format.channels,
            sample.audio_format.width,
            sample.audio_format.rate,
        )
        play_obj = wave_obj.play()
        play_obj.wait_done()


@dataclass
class PlayConfig(Coqpit):
    source: str = field(
        default="",
        metadata=dict(
            help="Sample DB, CSV or WAV file to play samples from",
        ),
    )
    parser.add_argument(
        "source", help="Sample DB, CSV or WAV file to play samples from"
    )
    parser.add_argument(
        "--start",
        type=int,
        default=0,
        metadata=dict(
            help="Sample index to start at (negative numbers are relative to the end of the collection)",
        ),
    )
    number: int = field(
        default=-1,
        metadata=dict(
            help="Number of samples to play (-1 for endless)",
        ),
    )
    random: bool = field(
        default=False,
        metadata=dict(
            help="If samples should be played in random order",
        ),
    )
    parser.add_argument(
        "--augment",
        action="append",
        help="Add an augmentation operation",
    )
    parser.add_argument(
        "--clock",
        type=float,
        default=0.5,
        help="Simulates clock value used for augmentations during training."
        "Ranges from 0.0 (representing parameter start values) to"
        "1.0 (representing parameter end values)",
    )
    pipe: bool = field(
        default=False,
        metadata=dict(
            help="Pipe first sample as wav file to stdout. Forces --number to 1.",
        ),
    )
    quiet: bool = field(
        default=False,
        metadata=dict(
            help="No info logging to console",
        ),
    )
    augment: List[str] = field(
        default=None,
        metadata=dict(
            help='space-separated list of augmenations for training samples. Format is "--augment operation1[param1=value1, ...] operation2[param1=value1, ...] ..."'
        ),
    )

    def __post_init__(self):
        if not self.pipe:
            try:
                import simpleaudio
            except ModuleNotFoundError:
                raise RuntimeError(
                    'Unless using --pipe true, play.py requires Python package "simpleaudio" for playing samples'
                )

        self.augmentations = parse_augmentations(self.augment)


if __name__ == "__main__":
    CLI_ARGS = handle_args()
    if not CLI_ARGS.pipe:
        try:
            import simpleaudio
        except ModuleNotFoundError:
            print(
                'Unless using the --pipe flag, play.py requires Python package "simpleaudio" for playing samples'
            )
            sys.exit(1)
    try:
        play_collection()
    except KeyboardInterrupt:
        print(" Stopped")


if __name__ == "__main__":
    main()
