#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

if __name__ == "__main__":
    try:
        from coqui_stt_training import train as stt_train
    except ImportError:
        print("Training package is not installed. See training documentation.")
        raise

    stt_train.main()
