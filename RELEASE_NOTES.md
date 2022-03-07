# General

This is the 1.3.0 release for Coqui STT, the deep learning toolkit for speech-to-text. In accordance with [semantic versioning](https://semver.org/), this version is backwards compatible with previous 1.x versions. The compatibility guarantees of our semantic versioning cover the deployment APIs: the C API and all the official language bindings: Python, Node.JS/ElectronJS and Java/Android. You can get started today with Coqui STT 1.3.0 by following the steps in our [documentation](https://stt.readthedocs.io/).

Compatible pre-trained models are available in the [Coqui Model Zoo](https://coqui.ai/models).

We also include example audio files:

[audio-1.3.0.tar.gz](https://github.com/coqui-ai/STT/releases/download/v1.3.0/audio-1.3.0.tar.gz)

which can be used to test the engine, and checkpoint files for the English model (which are identical to the 1.0.0 checkpoint and provided here for convenience purposes):

[coqui-stt-1.3.0-checkpoint.tar.gz](https://github.com/coqui-ai/STT/releases/download/v1.3.0/coqui-stt-1.3.0-checkpoint.tar.gz)

which are under the Apache 2.0 license and can be used as the basis for further fine-tuning. Finally this release also includes a source code tarball:

[v1.3.0.tar.gz](https://github.com/coqui-ai/STT/archive/v1.3.0.tar.gz)

Under the [MPL-2.0 license](https://www.mozilla.org/en-US/MPL/2.0/). Note that this tarball is for archival purposes only since GitHub does not include submodules in the automatic tarballs. For usage and development with the source code, clone the repository using Git, following our [documentation](https://stt.readthedocs.io/).

# Notable changes

 - Added new experimental APIs for loading Coqui STT models from memory buffers

    This allows loading models without writing them to disk first, which can be useful for dynamic model loading as well as for handling packaging in mobile platforms

 - Added ElectronJS 16 support
 - Rewritten audio processing logic in iOS demo app
 - Added pre-built binaries for iOS/Swift bindings in CI

    With these two changes we're hoping to get more feedback from iOS developers on our Swift bindings and pre-built STT frameworks - how can we best package and distribute the bindings so that it feels native to Swift/iOS developers? If you have any feedback, join [our Gitter room](https://gitter.im/coqui-ai/STT)!

 - Extended the Multilingual LibriSpeech importer to support all languages in the dataset

    Supported languages: English, German, Dutch, French, Spanish, Italian, Portuguese, Polish

 - Exposed full metadata information for decoded samples when using the coqui_stt_ctcdecoder Python package

    This allows access to the entire information returned by the decoder in training code, meaning experimenting with new model architectures doesn't require adapting the C++ inference library to test your changes.

 - Added initial support for Apple Silicon in our pre-built binaries

     C/C++ pre-built libraries are universal, language bindings will be updated soon

 - Added support for FLAC files in training

# Documentation

Documentation is available on [stt.readthedocs.io](https://stt.readthedocs.io/).

# Contact/Getting Help

1. [GitHub Discussions](https://github.com/coqui-ai/STT/discussions/) - best place to ask questions, get support, and discuss anything related to 🐸STT with other users.
3. [Gitter](https://gitter.im/coqui-ai/) - You can also join our Gitter chat.
4. [Issues](https://github.com/coqui-ai/STT/issues) - If you have discussed a problem and identified a bug in 🐸STT, or if you have a feature request, please open an issue in our repo. Please make sure you search for an already existing issue beforehand!

# Contributors to 1.3.0 release

 - Alessio Placitelli
 - Danny Waser
 - Erik Ziegler
 - Han Xiao
 - Reuben Morais
 - Danny Waser

We’d also like to thank all the members of our [Gitter chat room](https://gitter.im/coqui-ai/STT) who have been helping to shape this release!
