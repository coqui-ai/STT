.. _supported-platforms-deployment:

Supported platforms
===================

Here we maintain the list of supported platforms for deployment.

Linux / AMD64
^^^^^^^^^^^^^^^^^^^^^^^^^
* x86-64 CPU with AVX/FMA (one can rebuild without AVX/FMA, but it might slow down performance)
* glibc >= 2.24, libstdc++6 >= 6.3
* TensorFlow Lite runtime

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
* TensorFlow Lite runtime
