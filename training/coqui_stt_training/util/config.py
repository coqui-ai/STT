from __future__ import absolute_import, division, print_function

import json
import os
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import List

import progressbar
from attrdict import AttrDict
from coqpit import MISSING, Coqpit, check_argument
from coqui_stt_ctcdecoder import Alphabet, UTF8Alphabet

from .augmentations import NormalizeSampleRate, parse_augmentations
from .auto_input import create_alphabet_from_sources, create_datasets_from_auto_input
from .gpu import get_available_gpus
from .helpers import parse_file_size
from .io import is_remote_path, open_remote, path_exists_remote


class _ConfigSingleton:
    _config = None

    def __getattr__(self, name):
        if _ConfigSingleton._config is None:
            raise RuntimeError("Global configuration not yet initialized.")
        if not hasattr(_ConfigSingleton._config, name):
            raise RuntimeError(
                "Configuration option {} not found in config.".format(name)
            )
        return getattr(_ConfigSingleton._config, name)


Config = _ConfigSingleton()  # pylint: disable=invalid-name


@dataclass
class BaseSttConfig(Coqpit):
    def __post_init__(self):
        import tensorflow.compat.v1 as tfv1

        # Augmentations
        self.augmentations = parse_augmentations(self.augment)
        if self.augmentations:
            print(f"Parsed augmentations: {self.augmentations}", file=sys.stderr)
        if self.augmentations and self.feature_cache and self.cache_for_epochs == 0:
            print(
                "Due to your feature-cache settings, augmentations of "
                "the first epoch will be repeated on all following epochs. "
                "This may lead to unintended over-fitting. "
                "You can use --cache_for_epochs <n_epochs> to invalidate "
                "the cache after a given number of epochs.",
                file=sys.stderr,
            )

        if self.normalize_sample_rate:
            self.augmentations = [NormalizeSampleRate(self.audio_sample_rate)] + self[
                "augmentations"
            ]

        # Caching
        if self.cache_for_epochs == 1:
            print(
                "--cache_for_epochs == 1 is (re-)creating the feature cache "
                "on every epoch but will never use it. You can either set "
                "--cache_for_epochs > 1, or not use feature caching at all.",
                file=sys.stderr,
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

        # Checkpoint dir logic
        if self.checkpoint_dir:
            # checkpoint_dir always overrides {save,load}_checkpoint_dir
            self.save_checkpoint_dir = self.checkpoint_dir
            self.load_checkpoint_dir = self.checkpoint_dir

        if self.load_train not in ["last", "best", "init", "auto"]:
            self.load_train = "auto"

        if self.load_evaluate not in ["last", "best", "auto"]:
            self.load_evaluate = "auto"

        # Set default summary dir
        if not self.summary_dir:
            self.summary_dir = os.path.join(self.save_checkpoint_dir, "summaries")

        # Standard session configuration that'll be used for all new sessions.
        self.session_config = tfv1.ConfigProto(
            allow_soft_placement=True,
            log_device_placement=self.log_placement,
            inter_op_parallelism_threads=self.inter_op_parallelism_threads,
            intra_op_parallelism_threads=self.intra_op_parallelism_threads,
            gpu_options=tfv1.GPUOptions(allow_growth=self.use_allow_growth),
        )

        # CPU device
        self.cpu_device = "/cpu:0"

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

        if self.bytes_output_mode and self.alphabet_config_path:
            raise RuntimeError(
                "You cannot set --alphabet_config_path *and* --bytes_output_mode"
            )
        elif self.bytes_output_mode:
            self.alphabet = UTF8Alphabet()
        elif self.alphabet_config_path:
            self.alphabet = Alphabet(self.alphabet_config_path)
            self.effective_alphabet_path = self.alphabet_config_path
        elif os.path.exists(loaded_checkpoint_alphabet_file):
            print(
                "I --alphabet_config_path not specified, but found an alphabet file "
                f"alongside specified checkpoint ({loaded_checkpoint_alphabet_file}). "
                "Will use this alphabet file for this run.",
                file=sys.stderr,
            )
            self.alphabet = Alphabet(loaded_checkpoint_alphabet_file)
            self.effective_alphabet_path = loaded_checkpoint_alphabet_file
        elif self.train_files and self.dev_files and self.test_files:
            # If all subsets are in the same folder and there's an alphabet file
            # alongside them, use it.
            self.alphabet = None
            sources = self.train_files + self.dev_files + self.test_files
            parents = set(Path(p).parent for p in sources)
            if len(parents) == 1:
                possible_alphabet = list(parents)[0] / "alphabet.txt"
                if possible_alphabet.exists():
                    print(
                        "I --alphabet_config_path not specified, but all input "
                        "datasets are present and in the same folder (--train_files, "
                        "--dev_files and --test_files), and an alphabet.txt file "
                        f"was found alongside the sets ({possible_alphabet}). "
                        "Will use this alphabet file for this run.",
                        file=sys.stderr,
                    )
                    self.alphabet = Alphabet(str(possible_alphabet))
                    self.effective_alphabet_path = possible_alphabet

            if not self.alphabet:
                # Generate alphabet automatically from input dataset, but only if
                # fully specified, to avoid confusion in case a missing set has extra
                # characters.
                print(
                    "I --alphabet_config_path not specified, but all input datasets are "
                    "present (--train_files, --dev_files, --test_files). An alphabet "
                    "will be generated automatically from the data and placed alongside "
                    f"the checkpoint ({saved_checkpoint_alphabet_file}).",
                    file=sys.stderr,
                )
                characters, alphabet = create_alphabet_from_sources(sources)
                print(
                    f"I Generated alphabet characters: {characters}.",
                    file=sys.stderr,
                )
                self.alphabet = alphabet
                self.effective_alphabet_path = saved_checkpoint_alphabet_file
        else:
            if not os.path.isdir(self.load_checkpoint_dir):
                raise RuntimeError(
                    "Missing checkpoint directory (--checkpoint_dir or --load_checkpoint_dir)"
                )

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

        # Geometric Constants
        # ===================

        # For an explanation of the meaning of the geometric constants
        # please refer to doc/Geometry.md

        # Number of MFCC features
        self.n_input = 26  # TODO: Determine this programmatically from the sample rate

        # The number of frames in the context
        self.n_context = (
            9  # TODO: Determine the optimal value using a validation data set
        )

        # Number of units in hidden layers
        self.n_hidden_1 = self.n_hidden

        self.n_hidden_2 = self.n_hidden

        self.n_hidden_5 = self.n_hidden

        # LSTM cell state dimension
        self.n_cell_dim = self.n_hidden

        # The number of units in the third layer, which feeds in to the LSTM
        self.n_hidden_3 = self.n_cell_dim

        # Dims in last layer = number of characters in alphabet plus one
        # +1 for CTC blank label
        self.n_hidden_6 = self.alphabet.GetSize() + 1

        # Size of audio window in samples
        if (self.feature_win_len * self.audio_sample_rate) % 1000 != 0:
            raise RuntimeError(
                "--feature_win_len value ({}) in milliseconds ({}) multiplied "
                "by --audio_sample_rate value ({}) must be an integer value. Adjust "
                "your --feature_win_len value or resample your audio accordingly."
                "".format(
                    self.feature_win_len,
                    self.feature_win_len / 1000,
                    self.audio_sample_rate,
                )
            )

        self.audio_window_samples = self.audio_sample_rate * (
            self.feature_win_len / 1000
        )

        # Stride for feature computations in samples
        if (self.feature_win_step * self.audio_sample_rate) % 1000 != 0:
            raise RuntimeError(
                "--feature_win_step value ({}) in milliseconds ({}) multiplied "
                "by --audio_sample_rate value ({}) must be an integer value. Adjust "
                "your --feature_win_step value or resample your audio accordingly."
                "".format(
                    self.feature_win_step,
                    self.feature_win_step / 1000,
                    self.audio_sample_rate,
                )
            )

        self.audio_step_samples = self.audio_sample_rate * (
            self.feature_win_step / 1000
        )

        if self.one_shot_infer and not path_exists_remote(self.one_shot_infer):
            raise RuntimeError(
                "Path specified in --one_shot_infer is not a valid file."
            )

        if self.train_cudnn and self.load_cudnn:
            raise RuntimeError(
                "Trying to use --train_cudnn, but --load_cudnn "
                "was also specified. The --load_cudnn flag is only "
                "needed when converting a CuDNN RNN checkpoint to "
                "a CPU-capable graph. If your system is capable of "
                "using CuDNN RNN, you can just specify the CuDNN RNN "
                "checkpoint normally with --save_checkpoint_dir."
            )

    # sphinx-doc: training_ref_flags_start
    train_files: List[str] = field(
        default_factory=list,
        metadata=dict(
            help="space-separated list of files specifying the datasets used for training. Multiple files will get merged. If empty, training will not be run."
        ),
    )
    dev_files: List[str] = field(
        default_factory=list,
        metadata=dict(
            help="space-separated list of files specifying the datasets used for validation. Multiple files will get reported separately. If empty, validation will not be run."
        ),
    )
    test_files: List[str] = field(
        default_factory=list,
        metadata=dict(
            help="space-separated list of files specifying the datasets used for testing. Multiple files will get reported separately. If empty, the model will not be tested."
        ),
    )
    metrics_files: List[str] = field(
        default_factory=list,
        metadata=dict(
            help="space-separated list of files specifying the datasets used for tracking of metrics (after validation step). Currently the only metric is the CTC loss but without affecting the tracking of best validation loss. Multiple files will get reported separately. If empty, metrics will not be computed."
        ),
    )
    auto_input_dataset: str = field(
        default="",
        metadata=dict(
            help="path to a single CSV file to use for training. Cannot be specified alongside --train_files, --dev_files, --test_files. Training/validation/testing subsets will be automatically generated from the input, alongside with an alphabet file, if not already present.",
        ),
    )

    vocab_file: str = field(
        default="",
        metadata=dict(
            help="For use with evaluate_flashlight - text file containing vocabulary of scorer, one word per line."
        ),
    )

    read_buffer: str = field(
        default="1MB",
        metadata=dict(
            help="buffer-size for reading samples from datasets (supports file-size suffixes KB, MB, GB, TB)"
        ),
    )
    feature_cache: str = field(
        default="",
        metadata=dict(
            help="cache MFCC features to disk to speed up future training runs on the same data. This flag specifies the path where cached features extracted from --train_files will be saved. If empty, or if online augmentation flags are enabled, caching will be disabled."
        ),
    )
    cache_for_epochs: int = field(
        default=0,
        metadata=dict(
            help='after how many epochs the feature cache is invalidated again - 0 for "never"'
        ),
    )
    shuffle_batches: bool = field(
        default=False,
        metadata=dict(
            help="reshuffle batches every epoch, starting after N epochs, where N is set by the shuffle_start flag."
        ),
    )
    shuffle_start: int = field(
        default=1,
        metadata=dict(help="epoch to start shuffling batches from (zero-based)."),
    )
    shuffle_buffer: int = field(
        default=1000,
        metadata=dict(
            help="how many batches to keep in shuffle buffer when shuffling batches."
        ),
    )

    feature_win_len: int = field(
        default=32,
        metadata=dict(help="feature extraction audio window length in milliseconds"),
    )
    feature_win_step: int = field(
        default=20,
        metadata=dict(help="feature extraction window step length in milliseconds"),
    )
    audio_sample_rate: int = field(
        default=16000, metadata=dict(help="sample rate value expected by model")
    )
    normalize_sample_rate: bool = field(
        default=True,
        metadata=dict(
            help="normalize sample rate of all train_files to --audio_sample_rate"
        ),
    )

    # Data Augmentation
    augment: List[str] = field(
        default=None,
        metadata=dict(
            help='space-separated list of augmenations for training samples. Format is "--augment operation1[param1=value1, ...] operation2[param1=value1, ...] ..."'
        ),
    )

    # Global Constants
    epochs: int = field(
        default=75,
        metadata=dict(
            help="how many epochs (complete runs through the train files) to train for"
        ),
    )

    dropout_rate: float = field(
        default=0.05, metadata=dict(help="dropout rate for feedforward layers")
    )
    dropout_rate2: float = field(
        default=-1.0,
        metadata=dict(help="dropout rate for layer 2 - defaults to dropout_rate"),
    )
    dropout_rate3: float = field(
        default=-1.0,
        metadata=dict(help="dropout rate for layer 3 - defaults to dropout_rate"),
    )
    dropout_rate4: float = field(
        default=0.0, metadata=dict(help="dropout rate for layer 4 - defaults to 0.0")
    )
    dropout_rate5: float = field(
        default=0.0, metadata=dict(help="dropout rate for layer 5 - defaults to 0.0")
    )
    dropout_rate6: float = field(
        default=-1.0,
        metadata=dict(help="dropout rate for layer 6 - defaults to dropout_rate"),
    )

    relu_clip: float = field(
        default=20.0, metadata=dict(help="ReLU clipping value for non-recurrent layers")
    )

    # Adam optimizer(http://arxiv.org/abs/1412.6980) parameters
    beta1: float = field(
        default=0.9, metadata=dict(help="beta 1 parameter of Adam optimizer")
    )
    beta2: float = field(
        default=0.999, metadata=dict(help="beta 2 parameter of Adam optimizer")
    )
    epsilon: float = field(
        default=1e-8, metadata=dict(help="epsilon parameter of Adam optimizer")
    )
    learning_rate: float = field(
        default=0.001, metadata=dict(help="learning rate of Adam optimizer")
    )

    # Batch sizes
    train_batch_size: int = field(
        default=1, metadata=dict(help="number of elements in a training batch")
    )
    dev_batch_size: int = field(
        default=1, metadata=dict(help="number of elements in a validation batch")
    )
    test_batch_size: int = field(
        default=1, metadata=dict(help="number of elements in a test batch")
    )

    export_batch_size: int = field(
        default=1,
        metadata=dict(help="number of elements per batch on the exported graph"),
    )

    # Memory test
    skip_batch_test: bool = field(
        default=False,
        metadata=dict(help="skip batch size memory test before training"),
    )

    # Performance
    inter_op_parallelism_threads: int = field(
        default=0,
        metadata=dict(
            help="number of inter-op parallelism threads - see tf.ConfigProto for more details. USE OF THIS FLAG IS UNSUPPORTED"
        ),
    )
    intra_op_parallelism_threads: int = field(
        default=0,
        metadata=dict(
            help="number of intra-op parallelism threads - see tf.ConfigProto for more details. USE OF THIS FLAG IS UNSUPPORTED"
        ),
    )
    use_allow_growth: bool = field(
        default=False,
        metadata=dict(
            help="use Allow Growth flag which will allocate only required amount of GPU memory and prevent full allocation of available GPU memory"
        ),
    )
    load_cudnn: bool = field(
        default=False,
        metadata=dict(
            help="Specifying this flag allows one to convert a CuDNN RNN checkpoint to a checkpoint capable of running on a CPU graph."
        ),
    )
    train_cudnn: bool = field(
        default=False,
        metadata=dict(
            help="use CuDNN RNN backend for training on GPU. Note that checkpoints created with this flag can only be used with CuDNN RNN, i.e. fine tuning on a CPU device will not work"
        ),
    )
    automatic_mixed_precision: bool = field(
        default=False,
        metadata=dict(
            help="whether to allow automatic mixed precision training. USE OF THIS FLAG IS UNSUPPORTED. Checkpoints created with automatic mixed precision training will not be usable without mixed precision."
        ),
    )

    # Sample limits
    limit_test: int = field(
        default=0,
        metadata=dict(
            help="maximum number of elements to use from test set - 0 means no limit"
        ),
    )

    # Sample order
    reverse_test: bool = field(
        default=False, metadata=dict(help="if to reverse sample order of the test set")
    )

    # Checkpointing
    checkpoint_dir: str = field(
        default="",
        metadata=dict(
            help="directory from which checkpoints are loaded and to which they are saved"
        ),
    )
    load_checkpoint_dir: str = field(
        default="",
        metadata=dict(help="directory in which checkpoints are stored"),
    )
    save_checkpoint_dir: str = field(
        default="",
        metadata=dict(help="directory to which checkpoints are saved"),
    )
    checkpoint_secs: int = field(
        default=600, metadata=dict(help="checkpoint saving interval in seconds")
    )
    max_to_keep: int = field(
        default=5,
        metadata=dict(help="number of checkpoint files to keep - default value is 5"),
    )
    load_train: str = field(
        default="auto",
        metadata=dict(
            help='what checkpoint to load before starting the training process. "last" for loading most recent epoch checkpoint, "best" for loading best validation loss checkpoint, "init" for initializing a new checkpoint, "auto" for trying several options.'
        ),
    )
    load_evaluate: str = field(
        default="auto",
        metadata=dict(
            help='what checkpoint to load for evaluation tasks (test epochs, model export, single file inference, etc). "last" for loading most recent epoch checkpoint, "best" for loading best validation loss checkpoint, "auto" for trying several options.'
        ),
    )

    # Transfer Learning
    drop_source_layers: int = field(
        default=0,
        metadata=dict(
            help="single integer for how many layers to drop from source model (to drop just output == 1, drop penultimate and output ==2, etc)"
        ),
    )

    # Exporting
    export_dir: str = field(
        default="",
        metadata=dict(
            help="directory in which exported models are stored - if omitted, the model won't get exported"
        ),
    )
    remove_export: bool = field(
        default=False, metadata=dict(help="whether to remove old exported models")
    )
    export_tflite: bool = field(
        default=True, metadata=dict(help="export a graph ready for TF Lite engine")
    )
    export_quantize: bool = field(
        default=True,
        metadata=dict(help="export a quantized model (optimized for size)"),
    )
    export_savedmodel: bool = field(
        default=False,
        metadata=dict(help="export model in TF SavedModel format"),
    )
    n_steps: int = field(
        default=16,
        metadata=dict(
            help="how many timesteps to process at once by the export graph, higher values mean more latency"
        ),
    )
    export_zip: bool = field(
        default=False,
        metadata=dict(help="export a TFLite model and package with LM and info.json"),
    )
    export_file_name: str = field(
        default="output_graph",
        metadata=dict(help="name for the exported model file name"),
    )
    export_beam_width: int = field(
        default=500,
        metadata=dict(help="default beam width to embed into exported graph"),
    )

    # Model metadata
    export_author_id: str = field(
        default="author",
        metadata=dict(
            help="author of the exported model. GitHub user or organization name used to uniquely identify the author of this model"
        ),
    )
    export_model_name: str = field(
        default="model",
        metadata=dict(
            help="name of the exported model. Must not contain forward slashes."
        ),
    )
    export_model_version: str = field(
        default="0.0.1",
        metadata=dict(
            help="semantic version of the exported model. See https://semver.org/. This is fully controlled by you as author of the model and has no required connection with Coqui STT versions"
        ),
    )

    def field_val_equals_help(val_desc):
        return field(default="<{}>".format(val_desc), metadata=dict(help=val_desc))

    export_contact_info: str = field_val_equals_help(
        "public contact information of the author. Can be an email address, or a link to a contact form, issue tracker, or discussion forum. Must provide a way to reach the model authors"
    )
    export_license: str = field_val_equals_help(
        "SPDX identifier of the license of the exported model. See https://spdx.org/licenses/. If the license does not have an SPDX identifier, use the license name."
    )
    export_language: str = field_val_equals_help(
        'language the model was trained on - IETF BCP 47 language tag including at least language, script and region subtags. E.g. "en-Latn-UK" or "de-Latn-DE" or "cmn-Hans-CN". Include as much info as you can without loss of precision. For example, if a model is trained on Scottish English, include the variant subtag: "en-Latn-GB-Scotland".'
    )
    export_min_stt_version: str = field_val_equals_help(
        "minimum Coqui STT version (inclusive) the exported model is compatible with"
    )
    export_max_stt_version: str = field_val_equals_help(
        "maximum Coqui STT version (inclusive) the exported model is compatible with"
    )
    export_description: str = field_val_equals_help(
        "Freeform description of the model being exported. Markdown accepted. You can also leave this flag unchanged and edit the generated .md file directly. Useful things to describe are demographic and acoustic characteristics of the data used to train the model, any architectural changes, names of public datasets that were used when applicable, hyperparameters used for training, evaluation results on standard benchmark datasets, etc."
    )

    # Reporting
    log_level: int = field(
        default=1,
        metadata=dict(
            help="log level for console logs - 0: DEBUG, 1: INFO, 2: WARN, 3: ERROR"
        ),
    )
    show_progressbar: bool = field(
        default=True,
        metadata=dict(
            help="Show progress for training, validation and testing processes. Log level should be > 0."
        ),
    )

    log_placement: bool = field(
        default=False,
        metadata=dict(
            help="whether to log device placement of the operators to the console"
        ),
    )
    report_count: int = field(
        default=5,
        metadata=dict(
            help="number of phrases for each of best WER, median WER and worst WER to print out during a WER report"
        ),
    )

    summary_dir: str = field(
        default="",
        metadata=dict(
            help='target directory for TensorBoard summaries - defaults to directory "summaries" within the checkpoint folder'
        ),
    )

    test_output_file: str = field(
        default="",
        metadata=dict(
            help="path to a file to save all src/decoded/distance/loss tuples generated during a test epoch"
        ),
    )

    # Geometry
    n_hidden: int = field(
        default=2048, metadata=dict(help="layer width to use when initialising layers")
    )
    layer_norm: bool = field(
        default=False,
        metadata=dict(
            help="wether to use layer-normalization after each fully-connected layer (except the last one)"
        ),
    )

    # Initialization
    random_seed: int = field(
        default=4568,
        metadata=dict(help="default random seed that is used to initialize variables"),
    )

    # Early Stopping
    early_stop: bool = field(
        default=False,
        metadata=dict(
            help="Enable early stopping mechanism over validation dataset. If validation is not being run, early stopping is disabled."
        ),
    )
    es_epochs: int = field(
        default=25,
        metadata=dict(
            help="Number of epochs with no improvement after which training will be stopped. Loss is not stored in the checkpoint so when checkpoint is revived it starts the loss calculation from start at that point"
        ),
    )
    es_min_delta: float = field(
        default=0.05,
        metadata=dict(
            help="Minimum change in loss to qualify as an improvement. This value will also be used in Reduce learning rate on plateau"
        ),
    )

    # Reduce learning rate on plateau
    reduce_lr_on_plateau: bool = field(
        default=False,
        metadata=dict(
            help="Enable reducing the learning rate if a plateau is reached. This is the case if the validation loss did not improve for some epochs."
        ),
    )
    plateau_epochs: int = field(
        default=10,
        metadata=dict(
            help="Number of epochs to consider for RLROP. Has to be smaller than es_epochs from early stopping"
        ),
    )
    plateau_reduction: float = field(
        default=0.1,
        metadata=dict(
            help="Multiplicative factor to apply to the current learning rate if a plateau has occurred."
        ),
    )
    force_initialize_learning_rate: bool = field(
        default=False,
        metadata=dict(
            help="Force re-initialization of learning rate which was previously reduced."
        ),
    )

    # Decoder
    bytes_output_mode: bool = field(
        default=False,
        metadata=dict(
            help="enable Bytes Output Mode mode. When this is used the model outputs UTF-8 byte values directly rather than using an alphabet mapping. The --alphabet_config_path option will be ignored. See the training documentation for more details."
        ),
    )
    alphabet_config_path: str = field(
        default="",
        metadata=dict(
            help="path to the configuration file specifying the alphabet used by the network. See the comment in data/alphabet.txt for a description of the format."
        ),
    )
    scorer_path: str = field(
        default="", metadata=dict(help="path to the external scorer file.")
    )
    beam_width: int = field(
        default=1024,
        metadata=dict(
            help="beam width used in the CTC decoder when building candidate transcriptions"
        ),
    )
    # TODO move these defaults into some sort of external (inheritable?) configuration
    lm_alpha: float = field(
        default=0.931289039105002,
        metadata=dict(
            help="the alpha hyperparameter of the CTC decoder. Language Model weight."
        ),
    )
    lm_beta: float = field(
        default=1.1834137581510284,
        metadata=dict(
            help="the beta hyperparameter of the CTC decoder. Word insertion weight."
        ),
    )
    cutoff_prob: float = field(
        default=1.0,
        metadata=dict(
            help="only consider characters until this probability mass is reached. 1.0 = disabled."
        ),
    )
    cutoff_top_n: int = field(
        default=300,
        metadata=dict(
            help="only process this number of characters sorted by probability mass for each time step. If bigger than alphabet size, disabled."
        ),
    )

    # Inference mode
    one_shot_infer: str = field(
        default=None,
        metadata=dict(
            help="one-shot inference mode: specify a wav file and the script will load the checkpoint and perform inference on it."
        ),
    )

    # Optimizer mode
    lm_alpha_max: int = field(
        default=5,
        metadata=dict(
            help="the maximum of the alpha hyperparameter of the CTC decoder explored during hyperparameter optimization. Language Model weight."
        ),
    )
    lm_beta_max: int = field(
        default=5,
        metadata=dict(
            help="the maximum beta hyperparameter of the CTC decoder explored during hyperparameter optimization. Word insertion weight."
        ),
    )
    n_trials: int = field(
        default=2400,
        metadata=dict(
            help="the number of trials to run during hyperparameter optimization."
        ),
    )
    # sphinx-doc: training_ref_flags_end


def initialize_globals_from_cli():
    c = BaseSttConfig.init_from_argparse(arg_prefix="")
    _ConfigSingleton._config = c  # pylint: disable=protected-access


def initialize_globals_from_args(**override_args):
    # Update Config with new args
    c = BaseSttConfig(**override_args)
    _ConfigSingleton._config = c  # pylint: disable=protected-access


def initialize_globals_from_instance(config):
    """Initialize Config singleton from an existing instance"""
    _ConfigSingleton._config = config  # pylint: disable=protected-access


# Logging functions
# =================


def prefix_print(prefix, message):
    print(prefix + ("\n" + prefix).join(message.split("\n")))


def log_debug(message):
    if Config.log_level == 0:
        prefix_print("D ", message)


def log_info(message):
    if Config.log_level <= 1:
        prefix_print("I ", message)


def log_warn(message):
    if Config.log_level <= 2:
        prefix_print("W ", message)


def log_error(message):
    if Config.log_level <= 3:
        prefix_print("E ", message)


def create_progressbar(*args, **kwargs):
    # Progress bars in stdout by default
    if "fd" not in kwargs:
        kwargs["fd"] = sys.stdout

    if Config.show_progressbar:
        return progressbar.ProgressBar(*args, **kwargs)

    return progressbar.NullBar(*args, **kwargs)


def log_progress(message):
    if not Config.show_progressbar:
        log_info(message)
