.. _supported-platforms-deployment:

Supported platforms
===================

Here we maintain the list of supported platforms for deployment.

*Note that 🐸 currently only provides packages for CPU deployment with Python 3.5 or higher on Linux. We're working to get the rest of our usually supported packages back up and running as soon as possible.*

Linux / AMD64 without GPU
^^^^^^^^^^^^^^^^^^^^^^^^^
* x86-64 CPU with AVX/FMA (one can rebuild without AVX/FMA, but it might slow down performance)
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

Linux / ARMv7
^^^^^^^^^^^^^
* Cortex-A53 compatible ARMv7 SoC with Neon support
* Raspbian Buster-compatible distribution
* TensorFlow Lite runtime (``stt-tflite`` packages)

Linux / Aarch64
^^^^^^^^^^^^^^^
* Cortex-A72 compatible Aarch64 SoC
* ARMbian Buster-compatible distribution
* TensorFlow Lite runtime (``stt-tflite`` packages)

Android / ARMv7
^^^^^^^^^^^^^^^
* ARMv7 SoC with Neon support
* Android 7.0-10.0
* NDK API level >= 21
* TensorFlow Lite runtime (``stt-tflite`` packages)

Android / Aarch64
^^^^^^^^^^^^^^^^^
* Aarch64 SoC
* Android 7.0-10.0
* NDK API level >= 21
* TensorFlow Lite runtime (``stt-tflite`` packages)

macOS / AMD64
^^^^^^^^^^^^^
* x86-64 CPU with AVX/FMA (one can rebuild without AVX/FMA, but it might slow down performance)
* macOS >= 10.10
* Full TensorFlow runtime (``stt`` packages)
* TensorFlow Lite runtime (``stt-tflite`` packages)

Windows / AMD64 without GPU
^^^^^^^^^^^^^^^^^^^^^^^^^^^
* x86-64 CPU with AVX/FMA (one can rebuild without AVX/FMA, but it might slow down performance)
* Windows Server >= 2012 R2 ; Windows >= 8.1
* Full TensorFlow runtime (``stt`` packages)
* TensorFlow Lite runtime (``stt-tflite`` packages)

Windows / AMD64 with GPU
^^^^^^^^^^^^^^^^^^^^^^^^
* x86-64 CPU with AVX/FMA (one can rebuild without AVX/FMA, but it might slow down performance)
* Windows Server >= 2012 R2 ; Windows >= 8.1
* CUDA 10.0 (and capable GPU)
* Full TensorFlow runtime (``stt`` packages)
* TensorFlow Lite runtime (``stt-tflite`` packages)
