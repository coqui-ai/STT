#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

import sys

import optuna
import tensorflow.compat.v1 as tfv1
from coqui_stt_ctcdecoder import Scorer
from coqui_stt_training.evaluate import evaluate
from coqui_stt_training.train import create_model, early_training_checks
from coqui_stt_training.util.config import (
    Config,
    initialize_globals_from_cli,
    log_error,
)
from coqui_stt_training.util.evaluate_tools import wer_cer_batch


def character_based():
    is_character_based = False
    scorer = Scorer(
        Config.lm_alpha, Config.lm_beta, Config.scorer_path, Config.alphabet
    )
    is_character_based = scorer.is_utf8_mode()
    return is_character_based


def objective(trial):
    Config.lm_alpha = trial.suggest_uniform("lm_alpha", 0, Config.lm_alpha_max)
    Config.lm_beta = trial.suggest_uniform("lm_beta", 0, Config.lm_beta_max)

    is_character_based = trial.study.user_attrs["is_character_based"]

    samples = []
    for step, test_file in enumerate(Config.test_files):
        tfv1.reset_default_graph()

        current_samples = evaluate([test_file], create_model)
        samples += current_samples

        # Report intermediate objective value.
        wer, cer = wer_cer_batch(current_samples)
        trial.report(cer if is_character_based else wer, step)

        # Handle pruning based on the intermediate value.
        if trial.should_prune():
            raise optuna.exceptions.TrialPruned()

    wer, cer = wer_cer_batch(samples)
    return cer if is_character_based else wer


def compute_lm_optimization() -> dict:
    is_character_based = character_based()

    study = optuna.create_study()
    study.set_user_attr("is_character_based", is_character_based)
    study.optimize(objective, n_jobs=1, n_trials=Config.n_trials)

    return {
        "lm_alpha": study.best_params.get("lm_alpha"),
        "lm_beta": study.best_params.get("lm_beta"),
        "wer": study.best_value,
    }


def main():
    initialize_globals_from_cli()
    early_training_checks()

    if not Config.scorer_path:
        log_error(
            "Missing --scorer_path: can't optimize scorer alpha and beta "
            "parameters without a scorer!"
        )
        sys.exit(1)

    if not Config.test_files:
        log_error(
            "You need to specify what files to use for evaluation via "
            "the --test_files flag."
        )
        sys.exit(1)

    results = compute_lm_optimization()
    print(
        "Best params: lm_alpha={} and lm_beta={} with WER={}".format(
            results.get("lm_alpha"),
            results.get("lm_beta"),
            results.get("wer"),
        )
    )


if __name__ == "__main__":
    main()
