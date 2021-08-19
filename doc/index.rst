.. Coqui STT documentation main file, created by
   sphinx-quickstart on Thu Feb  2 21:20:39 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. image:: https://raw.githubusercontent.com/coqui-ai/STT/main/images/coqui-STT-logo-green.png
  :alt: Coqui STT logo and wordmark

**Coqui STT** (🐸STT) is an open-source deep-learning toolkit for training and deploying speech-to-text models.

🐸STT is battle tested in both production and research 🚀


.. toctree::
   :maxdepth: 1
   :caption: Quick Reference

   DEPLOYMENT

   TRAINING_INTRO

   TRAINING_ADVANCED

   BUILDING

Quickstart: Deployment
^^^^^^^^^^^^^^^^^^^^^^

The fastest way to deploy a pre-trained 🐸STT model is with `pip` with Python 3.5 or higher (*Note - only Linux supported at this time. We are working to get our normally supported packages back up and running.*):

.. code-block:: bash

   # Create a virtual environment
   $ python3 -m venv venv-stt
   $ source venv-stt/bin/activate

   # Install 🐸STT
   $ python3 -m pip install -U pip
   $ python3 -m pip install stt

   # Download 🐸's pre-trained English models
   $ curl -LO https://github.com/coqui-ai/STT/releases/download/v0.9.3/coqui-stt-0.9.3-models.pbmm
   $ curl -LO https://github.com/coqui-ai/STT/releases/download/v0.9.3/coqui-stt-0.9.3-models.scorer

   # Download some example audio files
   $ curl -LO https://github.com/coqui-ai/STT/releases/download/v0.9.3/audio-0.9.3.tar.gz
   $ tar -xvf audio-0.9.3.tar.gz

   # Transcribe an audio file
   $ stt --model coqui-stt-0.9.3-models.pbmm --scorer coqui-stt-0.9.3-models.scorer --audio audio/2830-3980-0043.wav

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

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
