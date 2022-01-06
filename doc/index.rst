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
