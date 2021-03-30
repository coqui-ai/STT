[Home](README.md) | [Previous - Introduction](INTRO.md) | [Next - Formatting your training data](DATA_FORMATTING.md)

# About DeepSpeech

## Contents

- [About DeepSpeech](#about-deepspeech)
  * [Contents](#contents)
  * [What does DeepSpeech do?](#what-does-deepspeech-do-)
  * [How does DeepSpeech work?](#how-does-deepspeech-work-)
  * [How is DeepSpeech implemented?](#how-is-deepspeech-implemented-)

## What does DeepSpeech do?

DeepSpeech is a tool for automatically transcribing spoken audio. DeepSpeech takes digital audio as input and returns a "most likely" text transcript of that audio.

DeepSpeech is an implementation of the DeepSpeech algorithm developed by Baidu and presented in this research paper:

> Hannun, A., Case, C., Casper, J., Catanzaro, B., Diamos, G., Elsen, E., Prenger R, Satheesh S, Sengupta S, Coates A., & Ng, A. Y. (2014). Deep speech: Scaling up end-to-end speech recognition. [arXiv preprint arXiv:1412.5567](https://arxiv.org/pdf/1412.5567).

DeepSpeech can be used for two key activities related to speech recognition - _training_ and _inference_. Speech recognition _inference_ - the process of converting spoken audio to written text - relies on a _trained model_. DeepSpeech can be used, with appropriate hardware (GPU) to train a model using a set of voice data, known as a _corpus_. Then, _inference_ or _recognition_ can be performed using the trained model. DeepSpeech includes several pre-trained models.

**This Playbook is focused on helping you train your own model.**

## How does DeepSpeech work?

DeepSpeech takes a stream of audio as input, and converts that stream of audio into a sequence of characters in the designated alphabet. This conversion is made possible by two basic steps: First, the audio is converted into a sequence of probabilities over characters in the alphabet. Secondly, this sequence of probabilities is converted into a sequence of characters.

The first step is made possible by a [Deep Neural Network](https://en.wikipedia.org/wiki/Deep_learning#Deep_neural_networks), and the second step is made possible by an [N-gram](https://en.wikipedia.org/wiki/N-gram)language model. The neural network is trained on audio and corresponding text transcripts, and the N-gram language model is trained on a text corpus (which is often different from the text transcripts of the audio). The neural model is trained to predict the text from speech, and the language model is trained to predict text from preceding text. At a very high level, you can think of the first part (the acoustic model) as a phonetic transcriber, and the second part (the language model) as a spelling and grammar checker.

## How is DeepSpeech implemented?

The core of DeepSpeech is written in C++, but it has bindings to Python, .NET, Java, JavaScript, and community-based bindings for Golang, Rust, Vlang, and NIM-lang.

---

[Home](README.md) | [Previous - Introduction](INTRO.md) | [Next - Formatting your training data](DATA_FORMATTING.md)
