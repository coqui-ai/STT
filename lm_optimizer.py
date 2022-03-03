#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

import sys

from coqui_stt_training.train import early_training_checks
from coqui_stt_training.util.config import (
    Config,
    initialize_globals_from_cli,
    log_error,
)

from coqui_stt_training.util import lm_optimize as lm_opt


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

    results = lm_opt.compute_lm_optimization()
    print(
        "Best params: lm_alpha={} and lm_beta={} with WER={}".format(
            results.get("lm_alpha"),
            results.get("lm_beta"),
            results.get("wer"),
        )
    )


if __name__ == "__main__":
    main()
