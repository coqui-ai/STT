# General

This is the 1.0.0 release for Coqui STT, the deep learning toolkit for speech-to-text. In accordance with [semantic versioning](https://semver.org/), this version is not completely backwards compatible with previous versions. The compatibility guarantees of our semantic versioning cover the inference APIs: the C API and all the official language bindings: Python, Node.JS/ElectronJS and Android. You can get started today with Coqui STT 1.0.0 by following the steps in our [documentation](https://stt.readthedocs.io/).

This release includes pre-trained English models, available in the Coqui Model Zoo:

 - [Coqui English STT v1.0.0-huge-vocab](https://coqui.ai/english/coqui/v1.0.0-huge-vocab)
 - [Coqui English STT v1.0.0-yesno](https://coqui.ai/english/coqui/v1.0.0-yesno)
 - [Coqui English STT v1.0.0-large-vocab](https://coqui.ai/english/coqui/v1.0.0-large-vocab)
 - [Coqui English STT v1.0.0-digits](https://coqui.ai/english/coqui/v1.0.0-digits)

all under the Apache 2.0 license.

The acoustic models were trained on American English data with synthetic noise augmentation. The model achieves a 4.5% word error rate on the [LibriSpeech clean test corpus](http://www.openslr.org/12) and 13.6% word error rate on the [LibriSpeech other test corpus](http://www.openslr.org/12) with the largest release language model.

Note that the model currently performs best in low-noise environments with clear recordings. This does not mean the model cannot be used outside of these conditions, but that accuracy may be lower. Some users may need to further fine tune the model to meet their intended use-case.

We also include example audio files:

[audio-1.0.0.tar.gz](https://github.com/coqui-ai/STT/releases/download/v1.0.0/audio-1.0.0.tar.gz)

which can be used to test the engine, and checkpoint files for the English model:

[coqui-stt-1.0.0-checkpoint.tar.gz](https://github.com/coqui-ai/STT/releases/download/v1.0.0/coqui-stt-1.0.0-checkpoint.tar.gz)

which are under the Apache 2.0 license and can be used as the basis for further fine-tuning. Finally this release also includes a source code tarball:

[v1.0.0.tar.gz](https://github.com/coqui-ai/STT/archive/v1.0.0.tar.gz)

Under the [MPL-2.0 license](https://www.mozilla.org/en-US/MPL/2.0/). Note that this tarball is for archival purposes only since GitHub does not include submodules in the automatic tarballs. For usage and development with the source code, clone the repository using Git, following our [documentation](https://stt.readthedocs.io/).


# Notable changes

 - Removed support for protocol buffer input in native client and consolidated all packages under a single "STT" name accepting TFLite inputs
 - Added programmatic interface to training code and example Jupyter Notebooks, including how to train with Common Voice data
 - Added transparent handling of mixed sample rates and stereo audio in training inputs
 - Moved CI setup to GitHub Actions, making code contributions easier to test
 - Added configuration management via Coqpit, providing a more flexible config interface that's compatible with Coqui TTS
 - Handle Opus audio files transparently in training inputs
 - Added support for automatic dataset subset splitting
 - Added support for automatic alphabet generation and loading
 - Started publishing the training code CI for a faster notebook setup
 - Refactor training code into self-contained modules and deprecate train.py as universal entry point for training

# Training Regimen + Hyperparameters for fine-tuning

The hyperparameters used to train the model are useful for fine tuning. Thus, we document them here along with the training regimen, hardware used (a server with 8 NVIDIA A100 GPUs each with 40GB of VRAM), along with the full training hyperparameters. The full training configuration in JSON format is available [here](https://gist.github.com/reuben/6ced6a8b41e3d0849dafb7cae301e905).

The datasets used were:
 - Common Voice 7.0 (with custom train/dev/test splits)
 - Multilingual LibriSpeech (English, Opus)
 - LibriSpeech

The optimal `lm_alpha` and `lm_beta` values with respect to the Common Voice 7.0 (custom Coqui splits) and a large vocabulary language model:

 - lm_alpha: 0.5891777425167632
 - lm_beta: 0.6619145283338659

# Documentation

Documentation is available on [stt.readthedocs.io](https://stt.readthedocs.io/).

# Contact/Getting Help

1. [GitHub Discussions](https://github.com/coqui-ai/STT/discussions/) - best place to ask questions, get support, and discuss anything related to 🐸STT with other users.
3. [Gitter](https://gitter.im/coqui-ai/) - You can also join our Gitter chat.
4. [Issues](https://github.com/coqui-ai/STT/issues) - If you have discussed a problem and identified a bug in 🐸STT, or if you have a feature request, please open an issue in our repo. Please make sure you search for an already existing issue beforehand!

# Contributors to 1.0.0 release

 - Alexandre Lissy
 - Anon-Artist
 - Anton Yaroshenko
 - Catalin Voss
 - CatalinVoss
 - dag7dev
 - Dustin Zubke
 - Eren Gölge
 - Erik Ziegler
 - Francis Tyers
 - Ideefixze
 - Ilnar Salimzianov
 - imrahul3610
 - Jeremiah Rose
 - Josh Meyer
 - Kathy Reid
 - Kelly Davis
 - Kenneth Heafield
 - NanoNabla
 - Neil Stoker
 - Reuben Morais
 - zaptrem

We’d also like to thank all the members of our [Gitter chat room](https://gitter.im/coqui-ai/STT) who have been helping to shape this release!
