.. _intro-training-docs:

Training: Quickstart
=====================

Introduction
------------

This document is a quickstart guide to training an 🐸STT model using your own speech data. For more in-depth training documentation, you should refer to :ref:`Advanced Training Topics <advanced-training-docs>`.

Training a model using your own audio can lead to better transcriptions compared to an off-the-shelf 🐸STT model. If your speech data differs significantly from the data we used in training, training your own model (or fine-tuning one of ours) may lead to large improvements in transcription quality. You can read about how speech characteristics interact with transcription accuracy :ref:`here <model-data-match>`.

Dockerfile Setup
----------------

We suggest you use our Docker image as a base for training. You can download and run the image in a container:

.. code-block:: bash

   $ docker pull ghcr.io/coqui-ai/stt-train
   $ docker run -it stt-train:latest

Alternatively you can build it from source using ``Dockerfile.train``, and run the locally built version in a container:

.. code-block:: bash

   $ git clone --recurse-submodules https://github.com/coqui-ai/STT
   $ cd STT
   $ docker build -f Dockerfile.train . -t stt-train:latest
   $ docker run -it stt-train:latest

You can read more about working with Dockerfiles in the `official documentation <https://docs.docker.com/engine/reference/builder/>`_.

Manual Setup
------------

If you don't want to use our Dockerfile template, you will need to manually install STT in order to train a model.

.. _training-deps:

Prerequisites
^^^^^^^^^^^^^

* `Python 3.6 <https://www.python.org/>`_
* Mac or Linux environment (training on Windows is *not* currently supported)
* CUDA 10.0 and CuDNN v7.6

Download
^^^^^^^^

We recommened that you clone the STT repo from the latest stable release branch on Github (e.g. ``v0.9.3``). You can find all 🐸STT releases `here <https://github.com/coqui-ai/STT/releases>`_).

.. code-block:: bash

   $ git clone --branch v0.9.3 --depth 1 https://github.com/coqui-ai/STT

Installation
^^^^^^^^^^^^

Installing STT and its dependencies is much easier with a virtual environment.

Set up Virtural Environment
"""""""""""""""""""""""""""

We recommend Python's built-in `venv <https://docs.python.org/3/library/venv.html>`_ module to manage your Python environment.

Setup your Python virtual environment, and name it ``coqui-stt-train-venv``:

.. code-block::

   $ python3 -m venv coqui-stt-train-venv

Activate the virtual environment:

.. code-block::

   $ source coqui-stt-train-venv/bin/activate

Setup with a ``conda`` virtual environment (Anaconda, Miniconda, or Mamba) is not guaranteed to work. Nevertheless, we're happy to review pull requests which fix any incompatibilities you encounter.

Install Dependencies and STT
""""""""""""""""""""""""""""

Now that we have cloned the STT repo from Github and setup a virtual environment with ``venv``, we can install STT and its dependencies. We recommend Python's built-in `pip <https://pip.pypa.io/en/stable/quickstart/>`_ module for installation:

.. code-block:: bash

   $ cd STT
   $ python3 -m pip install --upgrade pip wheel setuptools
   $ python3 -m pip install --upgrade -e .

The ``webrtcvad`` package may additionally require ``python3-dev``:

.. code-block:: bash

   $ sudo apt-get install python3-dev

If you have an NVIDIA GPU, it is highly recommended to install TensorFlow with GPU support. Training will be significantly faster than using the CPU.

.. code-block:: bash

   $ python3 -m pip uninstall tensorflow
   $ python3 -m pip install 'tensorflow-gpu==1.15.4'

Please ensure you have the required `CUDA dependency <https://www.tensorflow.org/install/source#gpu>`_ and :ref:`prerequisites <training-deps>`.

Verify Install
""""""""""""""

To verify that your installation was successful, run:

.. code-block:: bash

   $ ./bin/run-ldc93s1.sh

This script will train a model on a single audio file. If the script exits successfully, your STT training setup is ready. Congratulations!

Training on your own Data
-------------------------

Whether you used our Dockerfile template or you set up your own environment, the central STT training script is ``train.py``. For a list of command line options, use the ``--helpfull`` flag:

.. code-block:: bash

   $ cd STT
   $ python3 train.py --helpfull

Training Data
^^^^^^^^^^^^^

There's two kinds of data needed to train an STT model:

1. audio clips
2. text transcripts

Data Format
"""""""""""

Audio data is expected to be stored as WAV, sampled at 16kHz, and mono-channel. There's no hard expectations for the length of individual audio files, but in our experience, training is most successful when WAV files range from 5 to 20 seconds in length. Your training data should match as closely as possible the kind of speech you expect at deployment. You can read more about the significant characteristics of speech with regard to STT :ref:`here <model-data-match>`.

Text transcripts should be formatted exactly as the transcripts you expect your model to produce at deployment. If you want your model to produce capital letters, your transcripts should include capital letters. If you want your model to produce punctuation, your transcripts should include punctuation. Keep in mind that the more characters you include in your transcripts, the more difficult the task becomes for your model. STT models learn from experience, and if there's very few examples in the training data, the model will have a hard time learning rare characters (e.g. the "ï" in "naïve"). 

CSV file format
"""""""""""""""

The audio and transcripts used in training are passed to ``train.py`` via CSV files. You should supply CSV files for training (``train.csv``), development (``dev.csv``), and testing (``test.csv``). The CSV files should contain three columns:

1. ``wav_filename`` - the path to a WAV file on your machine
2. ``wav_filesize`` - the number of bytes in the WAV file
3. ``transcript`` - the text transcript of the WAV file

Start Training
^^^^^^^^^^^^^^

After you've successfully installed STT and have access to data, you can start a training run:

.. code-block:: bash

   $ cd STT
   $ python3 train.py --train_files train.csv --dev_files dev.csv --test_files test.csv

Next Steps
----------

You will want to customize the settings of ``train.py`` to work better with your data and your hardware. You should review the :ref:`command-line training flags <training-flags>`, and experiment with different settings.

For more in-depth training documentation, you should refer to the :ref:`Advanced Training Topics <advanced-training-docs>` section.
