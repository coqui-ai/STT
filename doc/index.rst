.. Coqui STT documentation main file, created by
   sphinx-quickstart on Thu Feb  2 21:20:39 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Coqui STT
=========

**Coqui STT** (🐸STT) is an open-source deep-learning toolkit for training and deploying speech-to-text models. 🐸STT is battle tested in both production and research 🚀

To install and use 🐸STT all you have to do is:

.. code-block:: bash

   # Create and activate a virtualenv
   virtualenv -p python3 $HOME/tmp/stt/
   source $HOME/tmp/stt/bin/activate

   # Install 🐸STT
   pip3 install stt

   # Download pre-trained English model files
   curl -LO https://github.com/coqui-ai/STT/releases/download/v0.9.3/coqui-stt-0.9.3-models.pbmm
   curl -LO https://github.com/coqui-ai/STT/releases/download/v0.9.3/coqui-stt-0.9.3-models.scorer

   # Download example audio files
   curl -LO https://github.com/coqui-ai/STT/releases/download/v0.9.3/audio-0.9.3.tar.gz
   tar xvf audio-0.9.3.tar.gz

   # Transcribe an audio file
   stt --model coqui-stt-0.9.3-models.pbmm --scorer coqui-stt-0.9.3-models.scorer --audio audio/2830-3980-0043.wav

A pre-trained English model is available for use and can be downloaded following the instructions in :ref:`the usage docs <usage-docs>`. For the latest release, including pre-trained models and checkpoints, `see the GitHub releases page <https://github.com/coqui-ai/STT/releases/latest>`_.

Quicker inference can be performed using a supported NVIDIA GPU on Linux. See the `release notes <https://github.com/coqui-ai/STT/releases/latest>`_ to find which GPUs are supported. To run ``stt`` on a GPU, install the GPU specific package:

.. code-block:: bash

   # Create and activate a virtualenv
   virtualenv -p python3 $HOME/tmp/coqui-stt-gpu-venv/
   source $HOME/tmp/coqui-stt-gpu-venv/bin/activate

   # Install 🐸STT CUDA enabled package
   pip3 install stt-gpu

   # Transcribe an audio file.
   stt --model coqui-stt-0.9.3-models.pbmm --scorer coqui-stt-0.9.3-models.scorer --audio audio/2830-3980-0043.wav

Please ensure you have the required :ref:`CUDA dependencies <cuda-inference-deps>`.

See the output of ``stt -h`` for more information on the use of ``stt``. (If you experience problems running ``stt``, please check :ref:`required runtime dependencies <runtime-deps>`).

.. toctree::
   :maxdepth: 2
   :caption: Introduction

   USING

   TRAINING

   SUPPORTED_PLATFORMS

   BUILDING

   BUILDING_DotNet

.. include:: ../SUPPORT.rst

.. toctree::
   :maxdepth: 2
   :caption: Decoder and scorer

   Decoder

   Scorer

.. toctree::
   :maxdepth: 2
   :caption: Architecture and training

   Architecture

   Geometry

   ParallelOptimization

.. toctree::
   :maxdepth: 3
   :caption: API Reference

   Error-Codes

   C-API

   DotNet-API

   Java-API

   NodeJS-API

   Python-API

.. toctree::
   :maxdepth: 2
   :caption: Examples

   C-Examples

   DotNet-Examples

   Java-Examples

   NodeJS-Examples

   Python-Examples
   
   HotWordBoosting-Examples

   Contributed-Examples

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
