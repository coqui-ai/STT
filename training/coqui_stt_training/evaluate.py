#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import json
import sys
from multiprocessing import cpu_count

import progressbar
import tensorflow.compat.v1 as tfv1
from coqui_stt_ctcdecoder import Scorer, ctc_beam_search_decoder_batch
from six.moves import zip

import tensorflow as tf

from .deepspeech_model import create_model, reset_default_graph
from .util.augmentations import NormalizeSampleRate
from .util.checkpoints import load_graph_for_evaluation
from .util.config import (
    Config,
    create_progressbar,
    initialize_globals_from_cli,
    log_error,
    log_progress,
)
from .util.evaluate_tools import calculate_and_print_report, save_samples_json
from .util.feeding import create_dataset
from .util.helpers import check_ctcdecoder_version


def sparse_tensor_value_to_texts(value, alphabet):
    r"""
    Given a :class:`tf.SparseTensor` ``value``, return an array of Python strings
    representing its values, converting tokens to strings using ``alphabet``.
    """
    return sparse_tuple_to_texts(
        (value.indices, value.values, value.dense_shape), alphabet
    )


def sparse_tuple_to_texts(sp_tuple, alphabet):
    indices = sp_tuple[0]
    values = sp_tuple[1]
    results = [[] for _ in range(sp_tuple[2][0])]
    for i, index in enumerate(indices):
        results[index[0]].append(values[i])
    # List of strings
    return [alphabet.Decode(res) for res in results]


def evaluate(test_csvs, create_model):
    if Config.scorer_path:
        scorer = Scorer(
            Config.lm_alpha, Config.lm_beta, Config.scorer_path, Config.alphabet
        )
    else:
        scorer = None

    test_sets = [
        create_dataset(
            [csv],
            batch_size=Config.test_batch_size,
            train_phase=False,
            augmentations=[NormalizeSampleRate(Config.audio_sample_rate)],
            reverse=Config.reverse_test,
            limit=Config.limit_test,
        )
        for csv in test_csvs
    ]
    iterator = tfv1.data.Iterator.from_structure(
        tfv1.data.get_output_types(test_sets[0]),
        tfv1.data.get_output_shapes(test_sets[0]),
        output_classes=tfv1.data.get_output_classes(test_sets[0]),
    )
    test_init_ops = [iterator.make_initializer(test_set) for test_set in test_sets]

    batch_wav_filename, (batch_x, batch_x_len), batch_y = iterator.get_next()

    # One rate per layer
    no_dropout = [None] * 6
    logits, _ = create_model(
        batch_x=batch_x, seq_length=batch_x_len, dropout=no_dropout
    )

    # Transpose to batch major and apply softmax for decoder
    transposed = tf.nn.softmax(tf.transpose(a=logits, perm=[1, 0, 2]))

    loss = tfv1.nn.ctc_loss(labels=batch_y, inputs=logits, sequence_length=batch_x_len)

    tfv1.train.get_or_create_global_step()

    # Get number of accessible CPU cores for this process
    try:
        num_processes = cpu_count()
    except NotImplementedError:
        num_processes = 1

    with tfv1.Session(config=Config.session_config) as session:
        load_graph_for_evaluation(session)

        def run_test(init_op, dataset):
            wav_filenames = []
            losses = []
            predictions = []
            ground_truths = []

            bar = create_progressbar(
                prefix="Test epoch | ",
                widgets=["Steps: ", progressbar.Counter(), " | ", progressbar.Timer()],
            ).start()
            log_progress("Test epoch...")

            step_count = 0

            # Initialize iterator to the appropriate dataset
            session.run(init_op)

            # First pass, compute losses and transposed logits for decoding
            while True:
                try:
                    (
                        batch_wav_filenames,
                        batch_logits,
                        batch_loss,
                        batch_lengths,
                        batch_transcripts,
                    ) = session.run(
                        [batch_wav_filename, transposed, loss, batch_x_len, batch_y]
                    )
                except tf.errors.OutOfRangeError:
                    break

                decoded = ctc_beam_search_decoder_batch(
                    batch_logits,
                    batch_lengths,
                    Config.alphabet,
                    Config.export_beam_width,
                    num_processes=num_processes,
                    scorer=scorer,
                    cutoff_prob=Config.cutoff_prob,
                    cutoff_top_n=Config.cutoff_top_n,
                )
                predictions.extend(d[0].transcript for d in decoded)
                ground_truths.extend(
                    sparse_tensor_value_to_texts(batch_transcripts, Config.alphabet)
                )
                wav_filenames.extend(
                    wav_filename.decode("UTF-8") for wav_filename in batch_wav_filenames
                )
                losses.extend(batch_loss)

                step_count += 1
                bar.update(step_count)

            bar.finish()

            # Print test summary
            test_samples = calculate_and_print_report(
                wav_filenames,
                ground_truths,
                predictions,
                losses,
                dataset,
                "cer" if Config.bytes_output_mode else "wer",
                Config.report_count,
            )
            return test_samples

        samples = []
        for csv, init_op in zip(test_csvs, test_init_ops):
            print("Testing model on {}".format(csv))
            samples.extend(run_test(init_op, dataset=csv))
        return samples


def test():
    reset_default_graph()

    samples = evaluate(Config.test_files, create_model)
    if Config.test_output_file:
        save_samples_json(samples, Config.test_output_file)


def main():
    initialize_globals_from_cli()
    check_ctcdecoder_version()

    if not Config.test_files:
        raise RuntimeError(
            "You need to specify what files to use for evaluation via "
            "the --test_files flag."
        )

    test()


if __name__ == "__main__":
    main()
