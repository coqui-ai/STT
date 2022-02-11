#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys

LOG_LEVEL_INDEX = sys.argv.index("--log_level") + 1 if "--log_level" in sys.argv else 0
DESIRED_LOG_LEVEL = (
    sys.argv[LOG_LEVEL_INDEX] if 0 < LOG_LEVEL_INDEX < len(sys.argv) else "3"
)
os.environ["TF_CPP_MIN_LOG_LEVEL"] = DESIRED_LOG_LEVEL

import numpy as np
import tensorflow as tf
import tensorflow.compat.v1 as tfv1

from coqui_stt_ctcdecoder import (
    flashlight_beam_search_decoder,
    Scorer,
    FlashlightDecoderState,
)
from .deepspeech_model import (
    create_inference_graph,
    create_overlapping_windows,
    reset_default_graph,
)
from .util.checkpoints import load_graph_for_evaluation
from .util.config import Config, initialize_globals_from_cli, log_error
from .util.feeding import audiofile_to_features


def do_single_file_inference(input_file_path):
    reset_default_graph()

    with open(Config.vocab_file) as fin:
        vocab = [w.encode("utf-8") for w in [l.strip() for l in fin]]

    with tfv1.Session(config=Config.session_config) as session:
        inputs, outputs, layers = create_inference_graph(batch_size=1, n_steps=-1)

        # Restore variables from training checkpoint
        load_graph_for_evaluation(session)

        features, features_len = audiofile_to_features(input_file_path)
        previous_state_c = np.zeros([1, Config.n_cell_dim])
        previous_state_h = np.zeros([1, Config.n_cell_dim])

        # Add batch dimension
        features = tf.expand_dims(features, 0)
        features_len = tf.expand_dims(features_len, 0)

        # Evaluate
        features = create_overlapping_windows(features).eval(session=session)
        features_len = features_len.eval(session=session)

        probs = layers["raw_logits"].eval(
            feed_dict={
                inputs["input"]: features,
                inputs["input_lengths"]: features_len,
                inputs["previous_state_c"]: previous_state_c,
                inputs["previous_state_h"]: previous_state_h,
            },
            session=session,
        )

        probs = np.squeeze(probs)

        if Config.scorer_path:
            scorer = Scorer(
                Config.lm_alpha, Config.lm_beta, Config.scorer_path, Config.alphabet
            )
        else:
            scorer = None
        decoded = flashlight_beam_search_decoder(
            probs,
            Config.alphabet,
            beam_size=Config.export_beam_width,
            decoder_type=FlashlightDecoderState.LexiconBased,
            token_type=FlashlightDecoderState.Aggregate,
            lm_tokens=vocab,
            scorer=scorer,
            cutoff_top_n=Config.cutoff_top_n,
        )
        # Print highest probability result
        print(" ".join(d.decode("utf-8") for d in decoded[0].words))


def main():
    initialize_globals_from_cli()

    if Config.one_shot_infer:
        do_single_file_inference(Config.one_shot_infer)
    else:
        raise RuntimeError(
            "Calling training_graph_inference script directly but no --one_shot_infer input audio file specified"
        )


if __name__ == "__main__":
    main()
