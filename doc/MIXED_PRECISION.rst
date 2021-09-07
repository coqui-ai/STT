.. _automatic-mixed-precision:

Automatic Mixed Precision
=========================

Training with `automatic mixed precision <https://medium.com/tensorflow/automatic-mixed-precision-in-tensorflow-for-faster-ai-training-on-nvidia-gpus-6033234b2540>`_ is available when training STT on an GPU.

Mixed precision training makes use of both ``FP32`` and ``FP16`` precisions where appropriate. ``FP16`` operations can leverage the Tensor cores on NVIDIA GPUs (Volta, Turing or newer architectures) for improved throughput. Mixed precision training often allows larger batch sizes. Automatic mixed precision training can be enabled by including the flag ``--automatic_mixed_precision true`` at training time:

.. code-block:: bash

    $ python -m coqui_stt_training.train \
        --train_files train.csv \
        --dev_files dev.csv \
        --test_files test.csv \
        --automatic_mixed_precision true

On a Volta generation V100 GPU, automatic mixed precision can speed up 🐸STT training and evaluation by approximately 30% to 40%.
