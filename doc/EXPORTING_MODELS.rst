.. _exporting-checkpoints:

Exporting a model for deployment
================================

After you train a STT model, your model will be stored on disk as a :ref:`checkpoint file <checkpointing>`. Model checkpoints are useful for resuming training at a later date, but they are not the correct format for deploying a model into production. The model format for deployment is a TFLite file.

This document explains how to export model checkpoints as a TFLite file.

How to export a model
---------------------

You can export STT model checkpoints for deployment by using the export script and the ``--export_dir`` flag.

.. code-block:: bash

   $ python3 -m coqui_stt_training.export \
         --checkpoint_dir path/to/existing/model/checkpoints \
         --export_dir where/to/export/model
