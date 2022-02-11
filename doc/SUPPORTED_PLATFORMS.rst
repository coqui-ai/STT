.. _supported-platforms-deployment:

Supported platforms
===================

<<<<<<< HEAD
<<<<<<< HEAD
Here we maintain the list of supported platforms for deployment.
=======
Here we maintain the list of supported platforms for running inference. Note that for now we only have working packages for Python on Linux, without GPU support. We're working to get the rest of our supported languages and architectures up and running.
>>>>>>> 3b0faaca (Note on supported platforms)
=======
Here we maintain the list of supported platforms for deployment.

<<<<<<< HEAD
*Note that 🐸STT currently only provides packages for CPU deployment with Python 3.5 or higher on Linux. We're working to get the rest of our usually supported packages back up and running as soon as possible.*
>>>>>>> 2d0a907e (Docs welcome page and Development / Inference page overhaul (#1793))

=======
>>>>>>> 6dcadde5 (Remove outdated comment in supported platforms doc [skip ci])
Linux / AMD64
^^^^^^^^^^^^^^^^^^^^^^^^^
* x86-64 CPU with AVX/FMA (one can rebuild without AVX/FMA, but it might slow down performance)
<<<<<<< HEAD
<<<<<<< HEAD
* glibc >= 2.24, libstdc++6 >= 6.3
* TensorFlow Lite runtime
=======
* Ubuntu 14.04+ (glibc >= 2.19, libstdc++6 >= 4.8)
* Full TensorFlow runtime (``stt`` packages)
* TensorFlow Lite runtime (``stt-tflite`` packages)

Linux / AMD64 with GPU
^^^^^^^^^^^^^^^^^^^^^^
* x86-64 CPU with AVX/FMA (one can rebuild without AVX/FMA, but it might slow down performance)
* Ubuntu 14.04+ (glibc >= 2.19, libstdc++6 >= 4.8)
* CUDA 10.0 (and capable GPU)
* Full TensorFlow runtime (``stt`` packages)
* TensorFlow Lite runtime (``stt-tflite`` packages)
>>>>>>> 2d0a907e (Docs welcome page and Development / Inference page overhaul (#1793))
=======
* glibc >= 2.24, libstdc++6 >= 6.3
* TensorFlow Lite runtime
>>>>>>> 9bc8d2e2 (Update supported architectures doc)

Linux / ARMv7
^^^^^^^^^^^^^
* Cortex-A53 compatible ARMv7 SoC with Neon support
* Raspbian Buster-compatible distribution
* TensorFlow Lite runtime

Linux / Aarch64
^^^^^^^^^^^^^^^
* Cortex-A72 compatible Aarch64 SoC
* ARMbian Buster-compatible distribution
* TensorFlow Lite runtime

Android / ARMv7
^^^^^^^^^^^^^^^
* ARMv7 SoC with Neon support
* Android 7.0-10.0
* NDK API level >= 21
* TensorFlow Lite runtime

Android / Aarch64
^^^^^^^^^^^^^^^^^
* Aarch64 SoC
* Android 7.0-10.0
* NDK API level >= 21
* TensorFlow Lite runtime

macOS / AMD64
^^^^^^^^^^^^^
* x86-64 CPU with AVX/FMA (one can rebuild without AVX/FMA, but it might slow down performance)
* macOS >= 10.10
* TensorFlow Lite runtime

Windows / AMD64
^^^^^^^^^^^^^^^^^^^^^^^^^^^
* x86-64 CPU with AVX/FMA (one can rebuild without AVX/FMA, but it might slow down performance)
* Windows Server >= 2012 R2 ; Windows >= 8.1
<<<<<<< HEAD
<<<<<<< HEAD
* TensorFlow Lite runtime
=======
* Full TensorFlow runtime (``stt`` packages)
* TensorFlow Lite runtime (``stt-tflite`` packages)

Windows / AMD64 with GPU
^^^^^^^^^^^^^^^^^^^^^^^^
* x86-64 CPU with AVX/FMA (one can rebuild without AVX/FMA, but it might slow down performance)
* Windows Server >= 2012 R2 ; Windows >= 8.1
* CUDA 10.0 (and capable GPU)
* Full TensorFlow runtime (``stt`` packages)
* TensorFlow Lite runtime (``stt-tflite`` packages)
>>>>>>> 2d0a907e (Docs welcome page and Development / Inference page overhaul (#1793))
=======
* TensorFlow Lite runtime
>>>>>>> 9bc8d2e2 (Update supported architectures doc)
