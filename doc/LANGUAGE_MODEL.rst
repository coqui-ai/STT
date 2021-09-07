.. _language-model:

How to Train a Language Model
=============================

Introduction
------------

This document explains how to train and package a language model for deployment.

You will usually want to deploy a language model in production. A good language model will improve transcription accuracy by correcting predictable spelling and grammatical mistakes. If you can predict what kind of speech your 🐸STT will encounter, you can make great gains in accuracy with a custom language model.

For example, if you want to transcribe university lectures on biology, you should train a language model on text related to biology. With this biology-specific language model, 🐸STT will be able to better recognize rare, hard to spell words like "cytokinesis".

How to train a model
--------------------

There are two steps to deploying a new language model for 🐸STT:

1. Identify and format text data for training
2. Train a `KenLM <https://github.com/kpu/kenlm>`_ language model using ``data/lm/generate_lm.py``
3. Package the model for deployment with ``generate_scorer_package``

Find Training Data
^^^^^^^^^^^^^^^^^^

Language models are trained from text, and the more similar that text is to the speech your 🐸STT system encounters at run-time, the better 🐸STT will perform for you.

For example, if you would like to transcribe the nightly news, then transcripts of past nightly news programs will be your best training data. If you'd like to transcribe an audio book, then the exact text of that book will create the best possible language model. If you want to put 🐸STT on a smart speaker, your training text corpus should include all the commands you make available to the user, such as "turn off the music" or "set an alarm for 5 minutes". If you can't predict the kind of speech 🐸STT will hear at run-time, then you should try to gather as much text as possible in your target language (e.g. Spanish).

Once you have identified text that is appropriate for your application, you should save it in a single file with one sentence per line. This text should not contain anything that a person wouldn't say, such as markup language.

Our release language model for English is generated from the LibriSpeech normalized training text, available `here <http://www.openslr.org/11>`_.

You can download the text with the following command:

.. code-block:: bash

    wget http://www.openslr.org/resources/11/librispeech-lm-norm.txt.gz

This LibriSpeech training text is around 4GB uncompressed, which should give you an idea of the size of a corpus needed for general speech recognition. For more constrained use cases with smaller vocabularies, you don't need as much data, but you should still try to gather as much as you can.

Train the Language Model
^^^^^^^^^^^^^^^^^^^^^^^^

Assuming you found and formatted a text corpus, the next step is to use that text to train a KenLM language model with ``data/lm/generate_lm.py``.

For more custom use cases, you might familiarize yourself with the `KenLM toolkit <https://kheafield.com/code/kenlm/>`_. Most of the options exposed by the ``generate_lm.py`` script are simply forwarded to KenLM options of the same name, so you should read the `KenLM documentation <https://kheafield.com/code/kenlm/estimation/>`_ in order to fully understand their behavior.

.. code-block:: bash

    python generate_lm.py \
      --input_txt librispeech-lm-norm.txt.gz \
      --output_dir . \
      --top_k 500000 \
      --kenlm_bins path/to/kenlm/build/bin/ \
      --arpa_order 5 \
      --max_arpa_memory "85%" \
      --arpa_prune "0|0|1" \
      --binary_a_bits 255 \
      --binary_q_bits 8 \
      --binary_type trie

``generate_lm.py`` will save the new language model as two files on disk: ``lm.binary`` and ``vocab-500000.txt``.

Package the Language Model for Deployment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Finally, we package the trained KenLM model for deployment with ``generate_scorer_package``. You can find pre-built binaries for ``generate_scorer_package`` on the official 🐸STT `release page <https://github.com/coqui-ai/STT/releases>`_ (inside ``native_client.*.tar.xz``). If for some reason you need to compile ``generate_scorer_package`` yourself, please refer to :ref:`build-generate-scorer-package`.

Package the language model for deployment with ``generate_scorer_package`` as such:

.. code-block:: bash

    ./generate_scorer_package \
      --alphabet ../alphabet.txt \
      --lm lm.binary \
      --vocab vocab-500000.txt \
      --package kenlm.scorer \
      --default_alpha 0.931289039105002 \
      --default_beta 1.1834137581510284

The ``--default_alpha`` and ``--default_beta`` parameters shown above were found with the ``lm_optimizer.py`` Python script.
