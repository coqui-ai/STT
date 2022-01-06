.. _usage-docs:

Deployment / Inference
======================

You might call the act of transcribing audio with a trained model either "deployment" or "inference". In this document we use "deployment", but we consider the terms interchangable.

Introduction
^^^^^^^^^^^^

Deployment is the process of feeding audio (speech) into a trained 🐸STT model and receiving text (transcription) as output. In practice you probably want to use two models for deployment: an audio model and a text model. The audio model (a.k.a. the acoustic model) is a deep neural network which converts audio into text. The text model (a.k.a. the language model / scorer) returns the likelihood of a string of text. If the acoustic model makes spelling or grammatical mistakes, the language model can help correct them.

You can deploy 🐸STT models either via a command-line client or a language binding.

* :ref:`The Python package + language binding <py-usage>`
* :ref:`The Node.JS package + language binding <nodejs-usage>`
* :ref:`The Android libstt AAR package <android-usage>`
* :ref:`The command-line client <cli-usage>`
* :ref:`The C API <c-usage>`

In some use cases, you might want to use the inference facilities built into the training code, for example for faster prototyping of new features. They are not production-ready, but because it's all Python code you won't need to recompile in order to test code changes, which can be much faster. See :ref:`checkpoint-inference` for more details.

.. _download-models:

Download trained Coqui STT models
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can find pre-trained models ready for deployment on the `Coqui Model Zoo <https://coqui.ai/models>`_. You can also use the 🐸STT Model Manager to download and try out the latest models:

.. code-block:: bash

   # Create a virtual environment
   $ python3 -m venv venv-stt
   $ source venv-stt/bin/activate

   # Install 🐸STT model manager
   $ python -m pip install -U pip
   $ python -m pip install coqui-stt-model-manager

   # Run the model manager. A browser tab will open and you can then download and test models from the Model Zoo.
   $ stt-model-manager

In every 🐸STT official release, there are different model files provided. The acoustic model uses the ``.tflite`` extension. Language models use the extension ``.scorer``. You can read more about language models with regard to :ref:`the decoding process <decoder-docs>` and :ref:`how scorers are generated <language-model>`.

.. _model-data-match:

How will a model perform on my data?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

How well a 🐸STT model transcribes your audio will depend on a lot of things. The general rule is the following: the more similar your data is to the data used to train the model, the better the model will transcribe your data. The more your data differs from the data used to train the model, the worse the model will perform on your data. This general rule applies to both the acoustic model and the language model. There are many dimensions upon which data can differ, but here are the most important ones:

* Language
* Accent
* Speaking style
* Speaking topic
* Speaker demographics

If you take a 🐸STT model trained on English, and pass Spanish into it, you should expect the model to perform horribly. Imagine you have a friend who only speaks English, and you ask her to make Spanish subtitles for a Spanish film, you wouldn't expect to get good subtitles. This is an extreme example, but it helps to form an intuition for what to expect from 🐸STT models. Imagine that the 🐸STT models are like people who speak a certain language with a certain accent, and then think about what would happen if you asked that person to transcribe your audio.

An acoustic model (i.e. ``.tflite`` file) has "learned" how to transcribe a certain language, and the model probably understands some accents better than others. In addition to languages and accents, acoustic models are sensitive to the style of speech, the topic of speech, and the demographics of the person speaking. The language model (``.scorer``) has been trained on text alone. As such, the language model is sensitive to how well the topic and style of speech matches that of the text used in training. The 🐸STT `release notes <https://github.com/coqui-ai/STT/releases/latest>`_ include detailed information on the data used to train the models. If the data used for training the off-the-shelf models does not align with your intended use case, it may be necessary to adapt or train new models in order to improve transcription on your data.

Training your own language model is often a good way to improve transcription on your audio. The process and tools used to generate a language model are described in :ref:`language-model` and general information can be found in :ref:`decoder-docs`. Generating a scorer from a constrained topic dataset is a quick process and can bring significant accuracy improvements if your audio is from a specific topic.

Acoustic model training is described in :ref:`intro-training-docs`. Fine tuning an off-the-shelf acoustic model to your own data can be a good way to improve performance. See the :ref:`fine tuning and transfer learning sections <training-fine-tuning>` for more information.

Model compatibility
^^^^^^^^^^^^^^^^^^^

🐸STT models are versioned to mitigate incompatibilities with clients and language bindings. If you get an error saying your model file version is too old for the client, you should either (1) upgrade to a newer model, (2) re-export your model from the checkpoint using a newer version of the code, or (3) downgrade your client if you need to use the old model and can't re-export it.

.. _py-usage:

Using the Python package
^^^^^^^^^^^^^^^^^^^^^^^^

Pre-built binaries for deploying a trained model can be installed with ``pip``. It is highly recommended that you use Python 3.6 or higher in a virtual environment. Both `pip <https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/#installing-pip>`_ and `venv <https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/#creating-a-virtual-environment>`_ are included in normal Python 3 installations.

When you create a new Python virtual environment, you create a directory containing a ``python`` binary and everything needed to run 🐸STT. For the purpose of this documentation, we will use on ``$HOME/coqui-stt-venv``, but you can use whatever directory you like.

Let's make the virtual environment:

.. code-block::

   $ python3 -m venv $HOME/coqui-stt-venv/

After this command completes, your new environment is ready to be activated. Each time you work with 🐸STT, you need to *activate* your virtual environment, as such:

.. code-block::

   $ source $HOME/coqui-stt-venv/bin/activate

After your environment has been activated, you can use ``pip`` to install ``stt``, as such:

.. code-block::

   (coqui-stt-venv)$ python -m pip install -U pip && python -m pip install stt

After installation has finished, you can call ``stt`` from the command-line.

The following command assumes you :ref:`downloaded the pre-trained models <download-models>`.

.. code-block:: bash

   (coqui-stt-venv)$ stt --model model.tflite --scorer huge-vocabulary.scorer --audio my_audio_file.wav

See :ref:`the Python client <py-api-example>` for an example of how to use the package programatically.

.. _nodejs-usage:

Using the Node.JS / Electron.JS package
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

*Note that 🐸STT currently only provides packages for CPU deployment with Python 3.5 or higher on Linux. We're working to get the rest of our usually supported packages back up and running as soon as possible.*

You can download the JS bindings using ``npm``\ :

.. code-block:: bash

   npm install stt

Special thanks to `Huan - Google Developers Experts in Machine Learning (ML GDE) <https://github.com/huan>`_ for providing the STT project name on npmjs.org

Please note that as of now, we support:
 - Node.JS versions 4 to 13
 - Electron.JS versions 1.6 to 7.1

TypeScript support is also provided.

See the :ref:`TypeScript client <js-api-example>` for an example of how to use the bindings programatically.

.. _android-usage:

Using the Android AAR libstt package
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A pre-built ``libstt`` Android AAR package can be downloaded from GitHub Releases, for Android versions 7.0+. In order to use it in your Android application, first modify your app's ``build.gradle`` file to add a local dir as a repository. In the ``repository`` section, add the following definition:

.. code-block:: groovy

   repositories {
       flatDir {
           dirs 'libs'
       }
   }

Then, create a libs directory inside your app's folder, and place the libstt AAR file there. Finally, add the following dependency declaration in your app's ``build.gradle`` file:

.. code-block:: groovy

   dependencies {
       implementation fileTree(dir: 'libs', include: ['*.aar'])
   }

This will link all .aar files in the ``libs`` directory you just created, including libstt.

.. _cli-usage:

Using the command-line client
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The pre-built binaries for the ``stt`` command-line (compiled C++) client are available in the ``native_client.*.tar.xz`` archive for your desired platform (where the * is the appropriate identifier for the platform you want to run on). You can download the archive from our `releases page <https://github.com/coqui-ai/STT/releases>`_.

Assuming you have :ref:`downloaded the pre-trained models <download-models>`, you can use the client as such:

.. code-block:: bash

   ./stt --model model.tflite --scorer huge-vocabulary.scorer --audio audio_input.wav

See the help output with ``./stt -h`` for more details.

.. _c-usage:

Using the C API
^^^^^^^^^^^^^^^

Alongside the pre-built binaries for the ``stt`` command-line client described :ref:`above <cli-usage>`, in the same ``native_client.*.tar.xz`` platform-specific archive, you'll find the ``coqui-stt.h`` header file as well as the pre-built shared libraries needed to use the 🐸STT C API. You can download the archive from our `releases page <https://github.com/coqui-ai/STT/releases>`_.

Then, simply include the header file and link against the shared libraries in your project, and you should be able to use the C API. Reference documentation is available in :ref:`c-api`.

Installing bindings from source
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If pre-built binaries aren't available for your system, you'll need to install them from scratch. Follow the :ref:`native client build and installation instructions <build-native-client>`.

Dockerfile for building from source
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We provide ``Dockerfile.build`` to automatically build ``libstt.so``, the C++ native client, Python bindings, and KenLM.

Before building, make sure that git submodules have been initialised:

.. code-block:: bash

   git submodule sync
   git submodule update --init

Then build with:

.. code-block:: bash

   docker build . -f Dockerfile.build -t stt-image

You can then use stt inside the Docker container:

.. code-block:: bash

   docker run -it stt-image bash


Runtime Dependencies
^^^^^^^^^^^^^^^^^^^^

Running ``stt`` may require runtime dependencies. Please refer to your system's documentation on how to install these dependencies.

* ``sox`` - The Python and Node.JS clients use SoX to resample files to 16kHz
* ``libgomp1`` - libsox (statically linked into the clients) depends on OpenMP
* ``libstdc++`` - Standard C++ Library implementation
* ``libpthread`` - Reported dependency on Linux. On Ubuntu, ``libpthread`` is part of the ``libpthread-stubs0-dev`` package
* ``Redistribuable Visual C++ 2015 Update 3 (64-bits)`` - Reported dependency on Windows. Please `download from Microsoft <https://www.microsoft.com/download/details.aspx?id=53587>`_

.. toctree::
   :maxdepth: 1

   SUPPORTED_PLATFORMS

.. Third party bindings
   ^^^^^^^^^^^^^^^^^^^^

   In addition to the official 🐸STT bindings and clients, third party developers have provided bindings to other languages:

   * `Asticode <https://github.com/asticode>`_ provides `Golang <https://golang.org>`_ bindings in its `go-astideepspeech <https://github.com/asticode/go-astideepspeech>`_ repo.
   * `RustAudio <https://github.com/RustAudio>`_ provide a `Rust <https://www.rust-lang.org>`_ binding, the installation and use of which is described in their `deepspeech-rs <https://github.com/RustAudio/deepspeech-rs>`_ repo.
   * `stes <https://github.com/stes>`_ provides preliminary `PKGBUILDs <https://wiki.archlinux.org/index.php/PKGBUILD>`_ to install the client and python bindings on `Arch Linux <https://www.archlinux.org/>`_ in the `arch-deepspeech <https://github.com/stes/arch-deepspeech>`_ repo.
   * `gst-deepspeech <https://github.com/Elleo/gst-deepspeech>`_ provides a `GStreamer <https://gstreamer.freedesktop.org/>`_ plugin which can be used from any language with GStreamer bindings.
   * `thecodrr <https://github.com/thecodrr>`_ provides `Vlang <https://vlang.io>`_ bindings. The installation and use of which is described in their `vspeech <https://github.com/thecodrr/vspeech>`_ repo.
   * `eagledot <https://gitlab.com/eagledot>`_ provides `NIM-lang <https://nim-lang.org/>`_ bindings. The installation and use of which is described in their `nim-deepspeech <https://gitlab.com/eagledot/nim-deepspeech>`_ repo.
