[Home](README.md) | [Previous - Deploying your model](DEPLOYMENT.md)

# Example applications of Coqui STT

## Contents

- [Example applications of Coqui STT](#example-applications-of-coqui-stt)
  * [Contents](#contents)
  * [Coqui STT worked examples repository](#coqui-stt-worked-examples-repository)
  * [Other suggestions for integrating Coqui STT](#other-suggestions-for-integrating-coqui-stt)
    + [A stand-alone transcription tool](#a-stand-alone-transcription-tool)
    + [Key Word Search in spoken audio](#key-word-search-in-spoken-audio)
    + [An interface to a voice-controlled application](#an-interface-to-a-voice-controlled-application)

## Coqui STT worked examples repository

There is a repository of examples of using 🐸STT for several use cases, including sample code, in the [🐸STT examples](https://github.com/coqui-ai/STT-examples/) repository.

The examples here include:

* [Android microphone streaming and transcription](https://github.com/coqui-ai/STT-examples/tree/r0.9/android_mic_streaming)

* [🐸STT running in an Electron app using ReactJS](https://github.com/coqui-ai/STT-examples/tree/r0.9/electron)

## Other suggestions for integrating Coqui STT

There are many other possibilities for incorporating speech recognition into your projects using 🐸STT.

### A stand-alone transcription tool

Accurate human-created transcriptions require someone who has been professionally trained, and their time is expensive. High quality transcription of audio may take up to 10 hours of transcription time per one hour of audio. With 🐸STT, you could increase transcriber productivity with a human-in-the-loop approach, in which 🐸STT generates a first-pass transcription, and the transcriber fixes any errors.

### Key Word Search in spoken audio

Key Word Search in audio is a simple task, but it takes considerable time. Given a collection of 100 hours of audio, if you only want to find all the instances of the word "coronavirus", instead of paying a professional transcriber, you might just pay someone to listen to all the audio and note when the word "coronavirus" was spoken. Nevertheless, you will still be paying for human time relative to the amount of audio you wish to search.

A better approach would be to modify 🐸STT to listen better for words of interest (e.g. "coronavirus") and run 🐸STT over all audio in parallel. Afterwards, a human may verify that the identified segments of audio contain the words of interest. This is another human-in-the-loop example, which makes the humans considerably more time-efficient.

### An interface to a voice-controlled application

Another example application of 🐸STT is as an interface to a voice-controlled application. This is an instance where a successful application (e.g. a digital assistant or smart speaker) cannot contain a human-in-the-loop. As such, 🐸STT is not making human-time more efficient, but rather, 🐸STT is enabling technologies which were previously not possible.

One example of a voice-controlled application using 🐸STT is the [voice add-on for WebThings.IO](https://github.com/WebThingsIO/voice-addon).

---

[Home](README.md) | [Previous - Deploying your model](DEPLOYMENT.md)
