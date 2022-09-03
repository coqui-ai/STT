# General

This is the 1.4.0 release for Coqui STT, the deep learning toolkit for speech-to-text. In accordance with [semantic versioning](https://semver.org/), this version is backwards compatible with previous 1.x versions. The compatibility guarantees of our semantic versioning cover the deployment APIs: the C API and all the official language bindings: Python, Node.JS/ElectronJS and Java/Android. You can get started with Coqui STT 1.4.0 by following the steps in our [documentation](https://stt.readthedocs.io/).

Compatible pre-trained models are available in the [Coqui Model Zoo](https://coqui.ai/models).

We also include example audio files:

[audio-1.4.0.tar.gz](https://github.com/coqui-ai/STT/releases/download/v1.4.0/audio-1.4.0.tar.gz)

which can be used to test the engine, and checkpoint files for the English model (which are identical to the 1.0.0 checkpoint and provided here for convenience purposes):

[coqui-stt-1.4.0-checkpoint.tar.gz](https://github.com/coqui-ai/STT/releases/download/v1.4.0/coqui-stt-1.4.0-checkpoint.tar.gz)

which are under the Apache 2.0 license and can be used as the basis for further fine-tuning. Finally this release also includes a source code tarball:

[v1.4.0.tar.gz](https://github.com/coqui-ai/STT/archive/v1.4.0.tar.gz)

Under the [MPL-2.0 license](https://www.mozilla.org/en-US/MPL/2.0/). Note that this tarball is for archival purposes only since GitHub does not include submodules in the automatic tarballs. For usage and development with the source code, clone the repository using Git, following our [documentation](https://stt.readthedocs.io/).

# Notable changes

 - Added experimental WebAssembly support

    [With the new WASM package you can deploy Coqui STT directly in the browser](https://github.com/coqui-ai/STT-examples/tree/r1.0/wasm).

 - Added ARMv7 and AArch64 Python wheels for Python 3.7 and 3.9
 - Migrated .NET bindings to .NET Framework 4.8
 - Rewritten audio processing logic in iOS demo app

# Documentation

Documentation is available on [stt.readthedocs.io](https://stt.readthedocs.io/).

# Contact/Getting Help

1. [GitHub Discussions](https://github.com/coqui-ai/STT/discussions/) - best place to ask questions, get support, and discuss anything related to 🐸STT with other users.
3. [Gitter](https://gitter.im/coqui-ai/) - You can also join our Gitter chat.
4. [Issues](https://github.com/coqui-ai/STT/issues) - If you have discussed a problem and identified a bug in 🐸STT, or if you have a feature request, please open an issue in our repo. Please make sure you search for an already existing issue beforehand!

# Contributors to 1.4.0 release

 - Alessio Placitelli
 - Anton Yaroshenko
 - ChamathKB
 - Ciaran O'Reilly
 - Daniel Souza
 - Danny Waser
 - David Roundy
 - Davidian1024
 - Edresson Casanova
 - Josh Meyer
 - Mariano Gonzalez
 - NanoNabla
 - Reuben Morais
 - Yanlong Wang

We’d also like to thank all the members of our [Gitter chat room](https://gitter.im/coqui-ai/STT) who have been helping to shape this release!
