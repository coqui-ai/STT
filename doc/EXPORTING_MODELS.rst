.. _exporting-checkpoints:

Exporting a model for deployment
================================

After you train a STT model, your model will be stored on disk as a :ref:`checkpoint file <checkpointing>`. Model checkpoints are useful for resuming training at a later date, but they are not the correct format for deploying a model into production. The best model format for deployment is a protobuf file.

This document explains how to export model checkpoints as a protobuf file.

How to export a model
---------------------

The simplest way to export STT model checkpoints for deployment is via ``train.py`` and the ``--export_dir`` flag.

.. code-block:: bash

   $ python3 train.py \
	--checkpoint_dir path/to/existing/model/checkpoints \
	--export_dir where/to/export/new/protobuf

However, you may want to export a model for small devices or for more efficient memory usage. In this case, follow the steps below.

Exporting as memory-mapped
^^^^^^^^^^^^^^^^^^^^^^^^^^

By default, the protobuf exported by ``train.py`` will be loaded in memory every time the model is deployed. This results in extra loading time and memory consumption. Creating a memory-mapped protobuf file will avoid these issues.

First, export your checkpoints to a protobuf with ``train.py``:

.. code-block:: bash

   $ python3 train.py \
	--checkpoint_dir path/to/existing/model/checkpoints \
	--export_dir where/to/export/new/protobuf

Second, convert the protobuf to a memory-mapped protobuf with ``convert_graphdef_memmapped_format``:

.. code-block::

   $ convert_graphdef_memmapped_format \
       --in_graph=output_graph.pb \
       --out_graph=output_graph.pbmm

``convert_graphdef_memmapped_format`` is a dedicated tool to convert regular protobuf files to memory-mapped protobufs. You can find this tool pre-compiled on the STT `release page <https://github.com/coqui-ai/STT/releases>`_. You should download and decompress ``convert_graphdef_memmapped_format`` before use. Upon a sucessful conversion ``convert_graphdef_memmapped_format`` will report conversion of a non-zero number of nodes.

Exporting for small devices
^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you want to deploy a STT model on a small device, you might consider exporting the model with `Tensorflow Lite <https://www.tensorflow.org/lite>`_ support. Export STT model checkpoints for Tensorflow Lite via ``train.py`` and the ``--export_tflite`` flag.

.. code-block:: bash

   $ python3 train.py \
	--checkpoint_dir path/to/existing/model/checkpoints \
	--export_dir where/to/export/new/protobuf \
	--export_tflite
