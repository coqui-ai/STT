#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import os
import sys
import json
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import tensorflow as tf
import tensorflow.compat.v1.logging as tflogging
tflogging.set_verbosity(tflogging.ERROR)
import logging
logging.getLogger('sox').setLevel(logging.ERROR)
import glob

from coqui_stt_training.util.audio import AudioFile
from coqui_stt_training.util.config import Config, initialize_globals
from coqui_stt_training.util.feeding import split_audio_file
from coqui_stt_training.util.flags import create_flags, FLAGS
from coqui_stt_training.util.logging import log_error, log_info, log_progress, create_progressbar
from coqui_stt_ctcdecoder import ctc_beam_search_decoder_batch, Scorer
from multiprocessing import Process, cpu_count


def fail(message, code=1):
    log_error(message)
    sys.exit(code)


def transcribe_file(audio_path, tlog_path):
    from coqui_stt_training.train import create_model  # pylint: disable=cyclic-import,import-outside-toplevel
    from coqui_stt_training.util.checkpoints import load_graph_for_evaluation
    initialize_globals()
    scorer = Scorer(FLAGS.lm_alpha, FLAGS.lm_beta, FLAGS.scorer_path, Config.alphabet)
    try:
        from coqui_stt_training import transcribe as stt_transcribe
    except ImportError:
        print("Training package is not installed. See training documentation.")
        raise

    stt_transcribe.main()
