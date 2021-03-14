.. _supported-platforms-inference:

Supported platforms
===================

Here we maintain the list of supported platforms for running inference.

Note that for now we only have working packages for Python on Linux for CPU. We are working to quickly get the rest of our usually supported languages and architectures up and running.

Linux / AMD64 without GPU
^^^^^^^^^^^^^^^^^^^^^^^^^
* x86-64 CPU with AVX/FMA (one can rebuild without AVX/FMA, but it might slow down inference)
* Ubuntu 14.04+ (glibc >= 2.19, libstdc++6 >= 4.8)
* Full TensorFlow runtime (``stt`` packages)
* TensorFlow Lite runtime (``stt-tflite`` packages)

Linux / AMD64 with GPU
^^^^^^^^^^^^^^^^^^^^^^
* x86-64 CPU with AVX/FMA (one can rebuild without AVX/FMA, but it might slow down inference)
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
* x86-64 CPU with AVX/FMA (one can rebuild without AVX/FMA, but it might slow down inference)
* macOS >= 10.10
* Full TensorFlow runtime (``stt`` packages)
* TensorFlow Lite runtime (``stt-tflite`` packages)

Windows / AMD64 without GPU
^^^^^^^^^^^^^^^^^^^^^^^^^^^
* x86-64 CPU with AVX/FMA (one can rebuild without AVX/FMA, but it might slow down inference)
* Windows Server >= 2012 R2 ; Windows >= 8.1
* Full TensorFlow runtime (``stt`` packages)
* TensorFlow Lite runtime (``stt-tflite`` packages)

Windows / AMD64 with GPU
^^^^^^^^^^^^^^^^^^^^^^^^
* x86-64 CPU with AVX/FMA (one can rebuild without AVX/FMA, but it might slow down inference)
* Windows Server >= 2012 R2 ; Windows >= 8.1
* CUDA 10.0 (and capable GPU)
* Full TensorFlow runtime (``stt`` packages)
* TensorFlow Lite runtime (``stt-tflite`` packages)
