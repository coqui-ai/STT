#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

import os
import sys
from dataclasses import dataclass, field

import optuna
from clearml import Task
from coqui_stt_ctcdecoder import Scorer
from coqui_stt_training.util.config import (
    BaseSttConfig,
    Config,
    initialize_globals_from_instance,
    log_error,
)
from coqui_stt_training.util.evaluate_tools import wer_cer_batch
from coqui_stt_training.evaluate_wav2vec2am import (
    compute_emissions,
    evaluate_from_emissions,
)


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
        current_samples = evaluate_from_emissions(
            Config.wav2vec2_model,
            test_file,
            trial.study.user_attrs["emissions"][step],
            Config.scorer_path,
            Config.scorer_alphabet,
            Config.num_processes,
            dump_to_file=None,
            beam_width=Config.export_beam_width,
            lm_alpha=Config.lm_alpha,
            lm_beta=Config.lm_beta,
        )
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

    emissions = []
    for step, test_file in enumerate(Config.test_files):
        emission = compute_emissions(
            Config.wav2vec2_model,
            test_file,
            Config.num_processes,
        )
        emissions.append(emission)

    study.set_user_attr("is_character_based", is_character_based)
    study.set_user_attr("emissions", emissions)
    study.optimize(objective, n_jobs=1, n_trials=Config.n_trials)

    return {
        "lm_alpha": study.best_params.get("lm_alpha"),
        "lm_beta": study.best_params.get("lm_beta"),
        "wer": study.best_value,
    }


@dataclass
class LmOptimizeWav2vec2amConfig(BaseSttConfig):
    wav2vec2_model: str = field(
        default="",
        metadata=dict(help="Path to exported ONNX model for wav2vec2 AM."),
    )
    scorer_alphabet: str = field(
        default="",
        metadata=dict(
            help="Path of alphabet file used for Scorer construction. Required if --scorer_path is specified"
        ),
    )
    num_processes: int = field(
        default=os.cpu_count(),
        metadata=dict(help="Number of worker processes for evaluation."),
    )
    clearml_project: str = field(
        default="STT/wav2vec2 decoding",
    )
    clearml_task: str = field(
        default="LM tuning",
    )


def initialize_config():
    config = LmOptimizeWav2vec2amConfig.init_from_argparse(arg_prefix="")
    task = Task.init(project_name=config.clearml_project, task_name=config.clearml_task)
    initialize_globals_from_instance(config)


def main():
    initialize_config()

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
