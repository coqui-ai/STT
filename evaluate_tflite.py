#!/usr/bin/env python
# -*- coding: utf-8 -*-

if __name__ == "__main__":

    print(
        "Using the top level evaluate_tflite.py script is deprecated and will be removed "
        "in a future release. Instead use: python -m coqui_stt_training.evaluate_export"
    )
    try:
        from coqui_stt_training import evaluate_export as stt_evaluate_export
    except ImportError:
        print("Training package is not installed. See training documentation.")
        raise

    stt_evaluate_export.main()
