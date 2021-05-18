# Coqui STT Playbook

A crash course on training speech recognition models using 🐸STT.

## Quick links

* [STT on GitHub](https://github.com/coqui-ai/STT)
* [STT documentation on ReadTheDocs](https://stt.readthedocs.io/en/latest/)
* [STT discussions on GitHub](https://github.com/coqui-ai/STT/discussions)
* [Common Voice Datasets](https://commonvoice.mozilla.org/en/datasets)
* [How to install Docker](https://docs.docker.com/engine/install/)

## [Introduction](INTRO.md)

Start here. This section will set your expectations for what you can achieve with the STT Playbook, and the prerequisites you'll need to start to train your own speech recognition models.

## [About Coqui STT](ABOUT.md)

Once you know what you can achieve with the STT Playbook, this section provides an overview of STT itself, its component parts, and how it differs from other speech recognition engines you may have used in the past.

## [Formatting your training data](DATA_FORMATTING.md)

Before you can train a model, you will need to collect and format your _corpus_ of data. This section provides an overview of the data format required for STT, and walks through an example in prepping a dataset from Common Voice.

## [The alphabet.txt file](ALPHABET.md)

If you are training a model that uses a different alphabet to English, for example a language with diacritical marks, then you will need to modify the `alphabet.txt` file.

## [Building your own scorer](SCORER.md)

Learn what the scorer does, and how you can go about building your own.

## [Acoustic model and language model](AM_vs_LM.md)

Learn about the differences between STT's _acoustic_ model and _language_ model and how they combine to provide end to end speech recognition.

## [Setting up your training environment](ENVIRONMENT.md)

This section walks you through building a Docker image, and spawning STT in a Docker container with persistent storage. This approach avoids the complexities of dependencies such as `tensorflow`.

## [Training a model](TRAINING.md)

Once you have your training data formatted, and your training environment established, this section will show you how to train a model, and provide guidance for overcoming common pitfalls.

## [Testing a model](TESTING.md)

Once you've trained a model, you will need to validate that it works for the context it's been designed for. This section walks you through this process.

## [Deploying your model](DEPLOYMENT.md)

Once trained and tested, your model is deployed. This section provides an overview of how you can deploy your model.

## [Applying STT to real world problems](EXAMPLES.md)

This section covers specific use cases where STT can be applied to real world problems, such as transcription, keyword searching and voice controlled applications.

---

## Introductory courses on machine learning

Providing an introduction to machine learning is beyond the scope of this PlayBook, howevever having an understanding of machine learning and deep learning concepts will aid your efforts in training speech recognition models with STT.

Here, we've linked to several resources that you may find helpful; they're listed in the order we recommend reading them in.

* [Digital Ocean's introductory machine learning tutorial](https://www.digitalocean.com/community/tutorials/an-introduction-to-machine-learning) provides an overview of different types of machine learning. The diagrams in this tutorial are a great way of explaining key concepts.

* [Google's machine learning crash course](https://developers.google.com/machine-learning/crash-course/ml-intro) provides a gentle introduction to the main concepts of machine learning, including _gradient descent_, _learning rate_, _training, test and validation sets_ and _overfitting_.

* If machine learning is something that sparks your interest, then you may enjoy [the MIT Open Learning Library's Introduction to Machine Learning course](https://openlearninglibrary.mit.edu/courses/course-v1:MITx+6.036+1T2019/course/), a 13-week college-level course covering perceptrons, neural networks, support vector machines and convolutional neural networks.

---

## How you can help provide feedback on the STT PlayBook

You can help to make the STT PlayBook even better by providing [via a GitHub Issue](https://github.com/coqui-ai/STT-playbook/issues)

* Please _try these instructions_, particularly for building a Docker image and running a Docker container, on multiple distributions of Linux so that we can identify corner cases.

* Please _contribute your tacit knowledge_ - such as:
  - common errors encountered in data formatting, environment setup, training and validation
  - techniques or approaches for improving the scorer, alphabet file or the accuracy of Word Error Rate (WER) and Character Error Rate (CER).
  - case studies of the work you or your organisation have been doing, showing your approaches to data validation, training or evaluation.

* Please identify errors in text - with many eyes, bugs are shallow :-)
