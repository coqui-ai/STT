# General

This is the 1.2.0 release for Coqui STT, the deep learning toolkit for speech-to-text. In accordance with [semantic versioning](https://semver.org/), this version is backwards compatible with previous 1.x versions. The compatibility guarantees of our semantic versioning cover the deployment APIs: the C API and all the official language bindings: Python, Node.JS/ElectronJS and Java/Android. You can get started today with Coqui STT 1.2.0 by following the steps in our [documentation](https://stt.readthedocs.io/).

Compatible pre-trained models are available in the [Coqui Model Zoo](https://coqui.ai/models).

We also include example audio files:

[audio-1.2.0.tar.gz](https://github.com/coqui-ai/STT/releases/download/v1.2.0/audio-1.2.0.tar.gz)

which can be used to test the engine, and checkpoint files for the English model (which are identical to the 1.0.0 checkpoint and provided here for convenience purposes):

[coqui-stt-1.2.0-checkpoint.tar.gz](https://github.com/coqui-ai/STT/releases/download/v1.2.0/coqui-stt-1.2.0-checkpoint.tar.gz)

which are under the Apache 2.0 license and can be used as the basis for further fine-tuning. Finally this release also includes a source code tarball:

[v1.2.0.tar.gz](https://github.com/coqui-ai/STT/archive/v1.2.0.tar.gz)

Under the [MPL-2.0 license](https://www.mozilla.org/en-US/MPL/2.0/). Note that this tarball is for archival purposes only since GitHub does not include submodules in the automatic tarballs. For usage and development with the source code, clone the repository using Git, following our [documentation](https://stt.readthedocs.io/).

# Notable changes

 - Added Python 3.10 support
 - Added [new inference APIs](https://stt.readthedocs.io/en/latest/search.html?q=flushbuffers&check_keywords=yes&area=default) which process any pending data before returning transcription results
 - Added an importer for using data from Common Voice's new personal data downloader, and [a Jupyter notebook which creates a custom STT model using your data](https://github.com/coqui-ai/STT/tree/main/notebooks#python-notebooks-for--stt)
 - Improved and extend evaluate_tflite script (now evaluate_export module) with Opus support
 - Added support for Ogg/Vorbis encoded audio files as training inputs
 - Added an importer for the Att-HACK dataset
 - Model dimensions are now loaded automatically from a checkpoint if present
 - Checkpoint loader will now handle CuDNN checkpoints transparently, without an explicit flag
 - When starting a training run, a batch size check will be performed automatically to help diagnose memory issues early
 - Added support for using WebDataset for training datasets
 - Updated to TensorFlow Lite 2.8, including [new XNNPACK optimizations for quantized models](https://blog.tensorflow.org/2021/09/faster-quantized-inference-with-xnnpack.html)

# Documentation

Documentation is available on [stt.readthedocs.io](https://stt.readthedocs.io/).

# Contact/Getting Help

1. [GitHub Discussions](https://github.com/coqui-ai/STT/discussions/) - best place to ask questions, get support, and discuss anything related to 🐸STT with other users.
3. [Gitter](https://gitter.im/coqui-ai/) - You can also join our Gitter chat.
4. [Issues](https://github.com/coqui-ai/STT/issues) - If you have discussed a problem and identified a bug in 🐸STT, or if you have a feature request, please open an issue in our repo. Please make sure you search for an already existing issue beforehand!

# Contributors to 1.2.0 release

 - Alexandre Lissy
 - Aya AlJafari
 - Danny Waser
 - Jeremiah Rose
 - Jonathan Washington
 - Josh Meyer
 - Reuben Morais
 - Vincent Fretin

We’d also like to thank all the members of our [Gitter chat room](https://gitter.im/coqui-ai/STT) who have been helping to shape this release!
