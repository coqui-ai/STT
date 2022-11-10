--------------
For Fabiennes model:
To run the model, click on Fabs_version_train_your_first_coqui_STT_model.ipynb
To run the original model, go to the folder "Notebooks" and choose the following: Train your first 🐸 STT model
In both cases the model can be opened by clicking "Open in Colab"

INSTRUCTIONS:
Using the Colab, every block can be run without adding or removing something.
First some necesarry stuff will be downloaded using pip.
Then the data is being donloaded and fromatted into something usable. This can take some time since it has some iterations to do.
Then you will be able to check if the data is how it is supposed to be. (To be certain you can look at how it should be on the original model, however only one sentence was used)
This is followed by setting the right configurations for the model.
Before testing the model, there is a training. The quality of the training depends on the amount of epochs. However, more epochs means more training time. Default is set at epoch = 100, which takes about an hour to train.
The last step is to test the model, in which the sentences from the audio's are being learned.

In the Colab file the instructions given are the ones with the original model, so not my own. These instructions are clear and give a good explanation of what is supposed to be done.

The original data only used one sentence to train the model. In my version 100 sentences are used. The dataset in which these sentences can be find is retrieved from HuggingFace and consist of validated English Common Voice data. Pulled from the data are the audio (.wav) and the sentences. To change the model from single sentence to multiple sentences many iteration processes where added for the downloading stage.

The model learns, using the transcribed sentences, what is said in the audio files. It wil give an overview of the name of the audio file, the sentence corresponding, and what the model understood the audio to say. Making use of more epoch makes the understanding of the model better. It makes some mistakes, but this could be due to the different voices used in the audio. Other than that is works as expected.
---------------

.. image:: images/coqui-STT-logo-green.png
   :alt: Coqui STT logo


.. |doc-img| image:: https://readthedocs.org/projects/stt/badge/?version=latest
   :target: https://stt.readthedocs.io/?badge=latest
   :alt: Documentation

.. |covenant-img| image:: https://img.shields.io/badge/Contributor%20Covenant-2.0-4baaaa.svg
   :target: CODE_OF_CONDUCT.md
   :alt: Contributor Covenant

.. |gitter-img| image:: https://badges.gitter.im/coqui-ai/STT.svg
   :target: https://gitter.im/coqui-ai/STT?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge
   :alt: Gitter Room

.. |doi| image:: https://zenodo.org/badge/344354127.svg
   :target: https://zenodo.org/badge/latestdoi/344354127

|doc-img| |covenant-img| |gitter-img| |doi|

`👉 Subscribe to 🐸Coqui's Newsletter <https://coqui.ai/?subscription=true>`_

**Coqui STT** (🐸STT) is a fast, open-source, multi-platform, deep-learning toolkit for training and deploying speech-to-text models. 🐸STT is battle tested in both production and research 🚀

🐸STT features
---------------

* High-quality pre-trained STT model.
* Efficient training pipeline with Multi-GPU support.
* Streaming inference.
* Multiple possible transcripts, each with an associated confidence score.
* Real-time inference.
* Small-footprint acoustic model.
* Bindings for various programming languages.

`Quickstart <https://stt.readthedocs.io/en/latest/#quickstart>`_
================================================================

Where to Ask Questions
----------------------

.. list-table::
   :widths: 25 25
   :header-rows: 1

   * - Type
     - Link
   * - 🚨 **Bug Reports**
     - `Github Issue Tracker <https://github.com/coqui-ai/STT/issues/>`_
   * - 🎁 **Feature Requests & Ideas**
     - `Github Issue Tracker <https://github.com/coqui-ai/STT/issues/>`_
   * - ❔ **Questions**
     - `Github Discussions <https://github.com/coqui-ai/stt/discussions/>`_
   * - 💬 **General Discussion**
     - `Github Discussions <https://github.com/coqui-ai/stt/discussions/>`_ or `Gitter Room <https://gitter.im/coqui-ai/STT?utm_source=share-link&utm_medium=link&utm_campaign=share-link>`_


Links & Resources
-----------------
.. list-table::
   :widths: 25 25
   :header-rows: 1

   * - Type
     - Link
   * - 📰 **Documentation**
     - `stt.readthedocs.io <https://stt.readthedocs.io/>`_
   * - 🚀 **Latest release with pre-trained models**
     - `see the latest release on GitHub <https://github.com/coqui-ai/STT/releases/latest>`_
   * - 🤝 **Contribution Guidelines**
     - `CONTRIBUTING.rst <CONTRIBUTING.rst>`_
