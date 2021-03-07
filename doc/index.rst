.. Coqui STT documentation main file, created by
   sphinx-quickstart on Thu Feb  2 21:20:39 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. image:: https://raw.githubusercontent.com/coqui-ai/STT/main/images/coqui-STT-logo-green.png
  :alt: Coqui STT logo and wordmark

**Coqui STT** (🐸STT) is an open-source deep-learning toolkit for training and deploying speech-to-text models. 🐸STT is battle tested in both production and research 🚀

For now we only have working packages for Python on Linux, without GPU support. We're working to get the rest of our supported languages and architectures up and running.

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

Quicker inference can be performed using a supported NVIDIA GPU on Linux. See the `release notes <https://github.com/coqui-ai/STT/releases/latest>`_ to find which GPUs are supported. To run ``stt`` on a GPU, install the GPU specific package. Note that for now the GPU package is not available. We're working to get all of our supported languages and architectures up and running.

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
   :maxdepth: 1
   :caption: Quick Reference

   DEPLOYMENT

   TRAINING_INTRO

   TRAINING_ADVANCED

   BUILDING

Quickstart
^^^^^^^^^^

The fastest way to use a pre-trained 🐸STT model is with the 🐸STT model manager, a tool that lets you quickly test and demo models locally. You'll need Python 3.6, 3.7, 3.8 or 3.9:

.. code-block:: bash

   # Create a virtual environment
   $ python3 -m venv venv-stt
   $ source venv-stt/bin/activate

   # Install 🐸STT model manager
   $ python -m pip install -U pip
   $ python -m pip install coqui-stt-model-manager

   # Run the model manager. A browser tab will open and you can then download and test models from the Model Zoo.
   $ stt-model-manager

.. toctree::
   :maxdepth: 1
   :caption: API Reference

   Error-Codes

   C-API

   DotNet-API

   Java-API

   NodeJS-API

   Python-API

.. toctree::
   :maxdepth: 1
   :caption: Examples

   Python-Examples

   NodeJS-Examples

   C-Examples

   DotNet-Examples

   Java-Examples

   HotWordBoosting-Examples

   Contributed-Examples

.. toctree::
   :maxdepth: 1
   :caption: Language Model

   LANGUAGE_MODEL

.. include:: SUPPORT.rst

.. toctree::
   :maxdepth: 1
   :caption: STT Playbook

   playbook/README

.. toctree::
   :maxdepth: 1
   :caption: Advanced topics

   DECODER

   Decoder-API

   PARALLEL_OPTIMIZATION


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
