[Home](README.md) | [Next - About Coqui STT](ABOUT.md)

# Introduction

## Contents

- [Introduction](#introduction)
  * [Contents](#contents)
  * [Is this guide for you?](#is-this-guide-for-you-)
  * [Setting expectations](#setting-expectations)
  * [Setting up for success](#setting-up-for-success)
  * [Checklist for success](#checklist-for-success)

## Is this guide for you?

You're probably here because you're interested in automatic speech recognition (ASR) - the process of converting phrases spoken by humans into written form. There have been significant advances in speech recognition in recent years, driven both by new deep learning algorithms, and by advances in hardware that are capable of the large volume of computations required by those algorithms. Several new tools are available to assist developers with both training speech recognition models and using those models for inference - 🐸STT being one of them.

If you're trying to get 🐸STT working for your application, your data, or a new language, you've come to the right place! You can easily download a pre-trained 🐸STT model for English, but it might not work for you out of the box. No worries, with a little tweaking you can get 🐸STT working for most anything!

Specifically, this guide will help you create a working 🐸STT model for a new language. Along the way, you will learn some best practices for speech recognition and data wrangling.

## Setting expectations

You might think that speech recognition is solved for English, and as such, with a little work you can solve speech recognition for a new language. This is false for two reasons. Firstly, speech recognition is far from solved for English, and secondly it is unlikely you will be able to create something that works as well as a pre-trained English 🐸STT model unless you have a few thousand hours of data.

Nevertheless, with some tips and tricks, you can still make create useful voice technology for a non-English language!

## Setting up for success

Speech recognition is a _statistical_ process. Speech recognition models are _trained_ on large amounts of voice data, using statistical techniques to "learn" associations between sounds, in the form of `.wav` files, and characters, that are found in an alphabet. Because speech recognition is statistical, it does not have "bugs" in the sense that computer code has bugs; instead, anomalies or biases in the data used for a speech recognition model mean that the resulting model will likely exhibit those biases.

Speech recognition still requires trial and error - with the data that is used to train a model, the language model or scorer that is used to form words from characters, and with specific training settings. "Debugging" speech recognition models means findings ways to make the data, the alphabet and and scorer more _accurate_. That is, making them mirror as closely as possible the real-world conditions in which the speech recognition model will be used. If your speech recognition model will be used to help transcribe geographic place names, then your voice data and your scorer need to cover those place names.

The success of any voice technology depends on a constellation of factors, and the accuracy of your speech recognizer is just one factor. To the extent that an existing voice technology works, it works because the creators have eliminated sources of failure. Think about one of the oldest working voice technologies: spoken digit recognition. When you call a bank you might hear a recording like this: "Say ONE to learn about credit cards, say TWO to learn about debit cards, or say ZERO to speak to a representative". These systems usually work well, but you might not know that if you answer with anything other than a single digit, the system will completely fail to understand you. Spoken digit recognition systems are setup for success because they've re-formulated an open-ended transcription problem as a simple classification problem. In this case, as long as the system is able to distinguish spoken digits from one another, it will succeed.

We will talk about ways in which you can constrain the search space of a problem and bias a model towards a set of words that you actually care about. If you want to make a useful digit recognizer, it doesn't matter if your model has an 85% Word Error Rate (WER) when transcribing the nightly news. All that matters is your model can correctly identify spoken digits. It is key to align what you care about with what you are measuring.

If you have ever used a speech technology and it worked flawlessly, the creators of the product set themselves up for success. This is what you must also do in your application.

## Checklist for success

To help set you up for success, we've included a checklist below.

- [ ] Have a clear understanding of the intended _use case_. What phrases will be used in the use case that you want to recognise?
- [ ] Ensure as many audio samples as possible, and ensure that they cover all the phrases expected in the use case. Remember, you will need hundreds of hours of audio data for large vocabulary speech recognition.
- [ ] The language model (scorer) needs to include every word that will be expected to be spoken in your intended use case.
- [ ] The language model (scorer) should _exclude_ any words that are _not_ expected to be spoken in your intended use case, to constrain the model.
- [ ] If your intended use case will have background noise, then your voice data should have background noise.
- [ ] If your intended use case will need to recognise particular accents, then your voice data should contain those accents.
- [ ] You will need access to a Linux host with an NVIDIA GPU, and you should be comfortable operating in a `bash` environment.

---

[Home](README.md) | [Next - About Coqui STT](ABOUT.md)
