#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

if __name__ == "__main__":
    print(
        "Using the top level transcribe.py script is deprecated and will be removed "
        "in a future release. Instead use: python -m coqui_stt_training.transcribe"
    )
    try:
        from coqui_stt_training import transcribe as stt_transcribe
    except ImportError:
        print("Training package is not installed. See training documentation.")
        raise

    stt_transcribe.main()
