from __future__ import absolute_import, division, print_function

import json
import os
import sys

import progressbar
import tensorflow.compat.v1 as tfv1
from attrdict import AttrDict
from coqui_stt_ctcdecoder import Alphabet, UTF8Alphabet
from xdg import BaseDirectory as xdg

import tensorflow.compat.v1 as tfv1

from .augmentations import NormalizeSampleRate, parse_augmentations
from .flags import FLAGS
from .gpu import get_available_gpus
from .helpers import parse_file_size
from .io import path_exists_remote
from .logging import log_error, log_warn



class _ConfigSingleton:
    _config = None

    def __getattr__(self, name):
        if _ConfigSingleton._config is None:
            raise RuntimeError("Global configuration not yet initialized.")
        if not hasattr(ConfigSingleton._config, name):
            raise RuntimeError(
                "Configuration option {} not found in config.".format(name)
            )
        return ConfigSingleton._config[name]


Config = ConfigSingleton()  # pylint: disable=invalid-name



    # Augmentations
    c.augmentations = parse_augmentations(FLAGS.augment)
    if c.augmentations and FLAGS.feature_cache and FLAGS.cache_for_epochs == 0:
        log_warn(
            "Due to current feature-cache settings the exact same sample augmentations of the first "
            "epoch will be repeated on all following epochs. This could lead to unintended over-fitting. "
            "You could use --cache_for_epochs <n_epochs> to invalidate the cache after a given number of epochs."
        )

    if FLAGS.normalize_sample_rate:
        c.augmentations = [NormalizeSampleRate(FLAGS.audio_sample_rate)] + c[
            "augmentations"
        ]

    # Caching
    if FLAGS.cache_for_epochs == 1:
        log_warn(
            "--cache_for_epochs == 1 is (re-)creating the feature cache on every epoch but will never use it."
        )

        # Read-buffer
        self.read_buffer = parse_file_size(self.read_buffer)

        # Set default dropout rates
        if self.dropout_rate2 < 0:
            self.dropout_rate2 = self.dropout_rate
        if self.dropout_rate3 < 0:
            self.dropout_rate3 = self.dropout_rate
        if self.dropout_rate6 < 0:
            self.dropout_rate6 = self.dropout_rate

    # Set default checkpoint dir
    if not FLAGS.checkpoint_dir:
        FLAGS.checkpoint_dir = xdg.save_data_path(os.path.join("stt", "checkpoints"))

    if FLAGS.load_train not in ["last", "best", "init", "auto"]:
        FLAGS.load_train = "auto"

    if FLAGS.load_evaluate not in ["last", "best", "auto"]:
        FLAGS.load_evaluate = "auto"

    # Set default summary dir
    if not FLAGS.summary_dir:
        FLAGS.summary_dir = xdg.save_data_path(os.path.join("stt", "summaries"))

    # Standard session configuration that'll be used for all new sessions.
    c.session_config = tfv1.ConfigProto(
        allow_soft_placement=True,
        log_device_placement=FLAGS.log_placement,
        inter_op_parallelism_threads=FLAGS.inter_op_parallelism_threads,
        intra_op_parallelism_threads=FLAGS.intra_op_parallelism_threads,
        gpu_options=tfv1.GPUOptions(allow_growth=FLAGS.use_allow_growth),
    )

    # CPU device
    c.cpu_device = "/cpu:0"

        # Available GPU devices
        self.available_devices = get_available_gpus(self.session_config)

        # If there is no GPU available, we fall back to CPU based operation
        if not self.available_devices:
            self.available_devices = [self.cpu_device]

        # If neither `--alphabet_config_path` nor `--bytes_output_mode` were specified,
        # look for alphabet file alongside loaded checkpoint.
        loaded_checkpoint_alphabet_file = os.path.join(
            self.load_checkpoint_dir, "alphabet.txt"
        )
        saved_checkpoint_alphabet_file = os.path.join(
            self.save_checkpoint_dir, "alphabet.txt"
        )

        if not (
            bool(self.auto_input_dataset)
            != (self.train_files or self.dev_files or self.test_files)
        ):
            raise RuntimeError(
                "When using --auto_input_dataset, do not specify --train_files, "
                "--dev_files, or --test_files."
            )

        if self.auto_input_dataset:
            (
                gen_train,
                gen_dev,
                gen_test,
                gen_alphabet,
            ) = create_datasets_from_auto_input(
                Path(self.auto_input_dataset),
                Path(self.alphabet_config_path) if self.alphabet_config_path else None,
            )
            self.train_files = [str(gen_train)]
            self.dev_files = [str(gen_dev)]
            self.test_files = [str(gen_test)]
            self.alphabet_config_path = str(gen_alphabet)

    # Number of MFCC features
    c.n_input = 26  # TODO: Determine this programmatically from the sample rate

    # The number of frames in the context
    c.n_context = 9  # TODO: Determine the optimal value using a validation data set

            raise RuntimeError(
                "Missing --alphabet_config_path flag. Couldn't find an alphabet file "
                "alongside checkpoint, and input datasets are not fully specified "
                "(--train_files, --dev_files, --test_files), so can't generate an alphabet. "
                "Either specify an alphabet file or fully specify the dataset, so one will "
                "be generated automatically."
            )

        if not self.save_checkpoint_dir:
            raise RuntimeError(
                "Missing checkpoint directory (--checkpoint_dir or --save_checkpoint_dir)"
            )

        # Save flags next to checkpoints
        if not is_remote_path(self.save_checkpoint_dir):
            os.makedirs(self.save_checkpoint_dir, exist_ok=True)
        flags_file = os.path.join(self.save_checkpoint_dir, "flags.txt")
        if not os.path.exists(flags_file):
            with open_remote(flags_file, "w") as fout:
                json.dump(self.serialize(), fout, indent=2)

        # Serialize alphabet alongside checkpoint
        if not os.path.exists(saved_checkpoint_alphabet_file):
            with open_remote(saved_checkpoint_alphabet_file, "wb") as fout:
                fout.write(self.alphabet.SerializeText())

        # If we have an existing checkpoint with a flags file, load its n_hidden value
        prev_flags_file = os.path.join(self.load_checkpoint_dir, "flags.txt")
        self.prev_n_hidden = None
        if os.path.exists(prev_flags_file):
            try:
                with open(prev_flags_file) as fin:
                    parsed = json.load(fin)
                prev_n_hidden = parsed["n_hidden"]

                if prev_n_hidden != self.n_hidden:
                    print(
                        f"W WARNING: --n_hidden value ({self.n_hidden}) is different "
                        f"from value found in checkpoint ({prev_n_hidden})."
                    )
                    print(
                        "W WARNING: This would result in an error when loading the "
                        "checkpoint, so n_hidden has been overriden with the "
                        "checkpoint value."
                    )
                    self.n_hidden = prev_n_hidden
            except json.JSONDecodeError:
                # File exists but is not JSON (older checkpoint), ignore error
                pass

    # Units in the sixth layer = number of characters in the target language plus one
    c.n_hidden_6 = c.alphabet.GetSize() + 1  # +1 for CTC blank label

    # Size of audio window in samples
    if (FLAGS.feature_win_len * FLAGS.audio_sample_rate) % 1000 != 0:
        log_error(
            "--feature_win_len value ({}) in milliseconds ({}) multiplied "
            "by --audio_sample_rate value ({}) must be an integer value. Adjust "
            "your --feature_win_len value or resample your audio accordingly."
            "".format(
                FLAGS.feature_win_len,
                FLAGS.feature_win_len / 1000,
                FLAGS.audio_sample_rate,
            )
        )
        sys.exit(1)

        # Number of MFCC features
        self.n_input = 26  # TODO: Determine this programmatically from the sample rate

    # Stride for feature computations in samples
    if (FLAGS.feature_win_step * FLAGS.audio_sample_rate) % 1000 != 0:
        log_error(
            "--feature_win_step value ({}) in milliseconds ({}) multiplied "
            "by --audio_sample_rate value ({}) must be an integer value. Adjust "
            "your --feature_win_step value or resample your audio accordingly."
            "".format(
                FLAGS.feature_win_step,
                FLAGS.feature_win_step / 1000,
                FLAGS.audio_sample_rate,
            )
        )
        sys.exit(1)

        # Number of units in hidden layers
        self.n_hidden_1 = self.n_hidden

    if FLAGS.one_shot_infer:
        if not path_exists_remote(FLAGS.one_shot_infer):
            log_error("Path specified in --one_shot_infer is not a valid file.")
            sys.exit(1)

    if FLAGS.train_cudnn and FLAGS.load_cudnn:
        log_error(
            "Trying to use --train_cudnn, but --load_cudnn "
            "was also specified. The --load_cudnn flag is only "
            "needed when converting a CuDNN RNN checkpoint to "
            "a CPU-capable graph. If your system is capable of "
            "using CuDNN RNN, you can just specify the CuDNN RNN "
            "checkpoint normally with --save_checkpoint_dir."
        )
        sys.exit(1)

        # LSTM cell state dimension
        self.n_cell_dim = self.n_hidden

        # The number of units in the third layer, which feeds in to the LSTM
        self.n_hidden_3 = self.n_cell_dim

    ConfigSingleton._config = c  # pylint: disable=protected-access
