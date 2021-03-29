.. _usage-docs:

Deployment / Inference
======================

You might call the act of transcribing audio with a trained model either "deployment" or "inference". In this document we use "deployment", but we consider the terms interchangable.

Introduction
^^^^^^^^^^^^

Deployment is the process of feeding audio (speech) into a trained 🐸STT model and receiving text (transcription) as output. In practice you probably want to use two models for deployment: an audio model and a text model. The audio model (a.k.a. the acoustic model) is a deep neural network which converts audio into text. The text model (a.k.a. the language model / scorer) returns the likelihood of a string of text. If the acoustic model makes spelling or grammatical mistakes, the language model can help correct them.

You can deploy 🐸STT models either via a command-line client or a language binding. 🐸 provides three language bindings and one command line client. There also exist several community-maintained clients and language bindings, which are listed `further down in this README <#third-party-bindings>`_.

*Note that 🐸STT currently only provides packages for CPU deployment with Python 3.5 or higher on Linux. We're working to get the rest of our usually supported packages back up and running as soon as possible.*

* :ref:`The Python package + language binding <py-usage>`
* :ref:`The command-line client <cli-usage>`
* :ref:`The native C API <c-usage>`
* :ref:`The Node.JS package + language binding <nodejs-usage>`
* :ref:`The .NET client + language binding <build-native-client-dotnet>`

.. _download-models:

Download trained Coqui STT models
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can find pre-trained models ready for deployment on the 🐸STT `releases page <https://github.com/coqui-ai/STT/releases>`_. You can also download the latest acoustic model (``.pbmm``) and language model (``.scorer``) from the command line as such:

.. code-block:: bash

   wget https://github.com/coqui-ai/STT/releases/download/v0.9.3/coqui-stt-0.9.3-models.pbmm
   wget https://github.com/coqui-ai/STT/releases/download/v0.9.3/coqui-stt-0.9.3-models.scorer

In every 🐸STT official release, there are several kinds of model files provided. For the acoustic model there are two file extensions: ``.pbmm`` and ``.tflite``. Files ending in ``.pbmm`` are compatible with clients and language bindings built against the standard TensorFlow runtime. ``.pbmm`` files are also compatible with CUDA enabled clients and language bindings. Files ending in ``.tflite``, on the other hand, are only compatible with clients and language bindings built against the `TensorFlow Lite runtime <https://www.tensorflow.org/lite/>`_. TFLite models are optimized for size and performance on low-power devices. You can find a full list of supported platforms and TensorFlow runtimes at :ref:`supported-platforms-deployment`.

For language models, there is only only file extension: ``.scorer``. Language models can run on any supported device, regardless of Tensorflow runtime. You can read more about language models with regard to :ref:`the decoding process <decoder-docs>` and :ref:`how scorers are generated <language-model>`.

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

An acoustic model (i.e. ``.pbmm`` or ``.tflite``) has "learned" how to transcribe a certain language, and the model probably understands some accents better than others. In addition to languages and accents, acoustic models are sensitive to the style of speech, the topic of speech, and the demographics of the person speaking. The language model (``.scorer``) has been trained on text alone. As such, the language model is sensitive to how well the topic and style of speech matches that of the text used in training. The 🐸STT `release notes <https://github.com/coqui-ai/STT/releases/tag/v0.9.3>`_ include detailed information on the data used to train the models. If the data used for training the off-the-shelf models does not align with your intended use case, it may be necessary to adapt or train new models in order to improve transcription on your data.

Training your own language model is often a good way to improve transcription on your audio. The process and tools used to generate a language model are described in :ref:`language-model` and general information can be found in :ref:`decoder-docs`. Generating a scorer from a constrained topic dataset is a quick process and can bring significant accuracy improvements if your audio is from a specific topic.

Acoustic model training is described in :ref:`intro-training-docs`. Fine tuning an off-the-shelf acoustic model to your own data can be a good way to improve performance. See the :ref:`fine tuning and transfer learning sections <training-fine-tuning>` for more information.

Model compatibility
^^^^^^^^^^^^^^^^^^^

🐸STT models are versioned to mitigate incompatibilities with clients and language bindings. If you get an error saying your model file version is too old for the client, you should either (1) upgrade to a newer model, (2) re-export your model from the checkpoint using a newer version of the code, or (3) downgrade your client if you need to use the old model and can't re-export it.

.. _py-usage:

Using the Python package
^^^^^^^^^^^^^^^^^^^^^^^^

Pre-built binaries for deploying a trained model can be installed with ``pip``. It is highly recommended that you use Python 3.5 or higher in a virtual environment. Both `pip <https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/#installing-pip>`_ and `venv <https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/#creating-a-virtual-environment>`_ are included in normal Python 3 installations.

When you create a new Python virtual environment, you create a directory containing a ``python`` binary and everything needed to run 🐸STT. For the purpose of this documentation, we will use on ``$HOME/coqui-stt-venv``, but you can use whatever directory you like.

Let's make the virtual environment:

.. code-block::

   $ python3 -m venv $HOME/coqui-stt-venv/

After this command completes, your new environment is ready to be activated. Each time you work with 🐸STT, you need to *activate* your virtual environment, as such:

.. code-block::

   $ source $HOME/coqui-stt-venv/bin/activate

After your environment has been activated, you can use ``pip`` to install ``stt``, as such:

.. code-block::

   (coqui-stt-venv)$ python3 -m pip install -U pip && python3 -m pip install stt

After installation has finished, you can call ``stt`` from the command-line.

The following command assumes you :ref:`downloaded the pre-trained models <download-models>`.

.. code-block:: bash

   (coqui-stt-venv)$ stt --model stt-0.9.3-models.pbmm --scorer stt-0.9.3-models.scorer --audio my_audio_file.wav

See :ref:`the Python client <py-api-example>` for an example of how to use the package programatically.

*GPUs will soon be supported:* If you have a supported NVIDIA GPU on Linux, you can install the GPU specific package as follows:

.. code-block::

   (coqui-stt-venv)$ python3 -m pip install -U pip && python3 -m pip install stt-gpu

See the `release notes <https://github.com/coqui-ai/STT/releases>`_ to find which GPUs are supported. Please ensure you have the required `CUDA dependency <#cuda-dependency>`_.

.. _cli-usage:

Using the command-line client
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To download the pre-built binaries for the ``stt`` command-line (compiled C++) client, use ``util/taskcluster.py``\ :

.. code-block:: bash

   python3 util/taskcluster.py --target .

or if you're on macOS:

.. code-block:: bash

   python3 util/taskcluster.py --arch osx --target .

also, if you need some binaries different than current main branch, like ``v0.2.0-alpha.6``\ , you can use ``--branch``\ :

.. code-block:: bash

   python3 util/taskcluster.py --branch "v0.2.0-alpha.6" --target "."

The script ``taskcluster.py`` will download ``native_client.tar.xz`` (which includes the ``stt`` binary and associated libraries) and extract it into the current folder. ``taskcluster.py`` will download binaries for Linux/x86_64 by default, but you can override that behavior with the ``--arch`` parameter. See the help info with ``python3 util/taskcluster.py -h`` for more details. Specific branches of 🐸STT or TensorFlow can be specified as well.

Alternatively you may manually download the ``native_client.tar.xz`` from the `releases page <https://github.com/coqui-ai/STT/releases>`_.

Assuming you have :ref:`downloaded the pre-trained models <download-models>`, you can use the client as such: 

.. code-block:: bash

   ./stt --model coqui-stt-0.9.3-models.pbmm --scorer coqui-stt-0.9.3-models.scorer --audio audio_input.wav

See the help output with ``./stt -h`` for more details.

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

If you're using Linux and have a supported NVIDIA GPU, you can install the GPU specific package as follows:

.. code-block:: bash

   npm install stt-gpu

See the `release notes <https://github.com/coqui-ai/STT/releases>`_ to find which GPUs are supported. Please ensure you have the required `CUDA dependency <#cuda-dependency>`_.

See the :ref:`TypeScript client <js-api-example>` for an example of how to use the bindings programatically.


Installing bindings from source
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If pre-built binaries aren't available for your system, you'll need to install them from scratch. Follow the :ref:`native client build and installation instructions <build-native-client>`.

Dockerfile for building from source
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We provide ``Dockerfile.build`` to automatically build ``libstt.so``, the C++ native client, Python bindings, and KenLM.

If you want to specify a different repository or branch, you can specify the ``STT_REPO`` or ``STT_SHA`` arguments:

.. code-block:: bash

   docker build . -f Dockerfile.build --build-arg STT_REPO=git://your/fork --build-arg STT_SHA=origin/your-branch

.. _runtime-deps:


Runtime Dependencies
^^^^^^^^^^^^^^^^^^^^

Running ``stt`` may require runtime dependencies. Please refer to your system's documentation on how to install these dependencies.

* ``sox`` - The Python and Node.JS clients use SoX to resample files to 16kHz
* ``libgomp1`` - libsox (statically linked into the clients) depends on OpenMP
* ``libstdc++`` - Standard C++ Library implementation
* ``libpthread`` - Reported dependency on Linux. On Ubuntu, ``libpthread`` is part of the ``libpthread-stubs0-dev`` package
* ``Redistribuable Visual C++ 2015 Update 3 (64-bits)`` - Reported dependency on Windows. Please `download from Microsoft <https://www.microsoft.com/download/details.aspx?id=53587>`_

CUDA Dependency
^^^^^^^^^^^^^^^

The GPU capable builds (Python, NodeJS, C++, etc) depend on CUDA 10.1 and CuDNN v7.6.

.. _cuda-inference-deps:

.. toctree::
   :maxdepth: 1
   :caption: Supported Platforms

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
