[Home](README.md) | [Previous - About Coqui STT](ABOUT.md) | [Next - The alphabet.txt file](ALPHABET.md)

# Formatting your training data for Coqui STT

## Contents

- [Formatting your training data for Coqui STT](#formatting-your-training-data-for-coqui-stt)
  * [Contents](#contents)
  * [Collecting data](#collecting-data)
  * [Preparing your data for training](#preparing-your-data-for-training)
    + [Data from Common Voice](#data-from-common-voice)
  * [Importers](#importers)

🐸STT expects audio files to be WAV format, mono-channel, and with a 16kHz sampling rate.

For training, testing, and development, you need to feed 🐸STT CSV files which contain three columns: `wav_filename,wav_filesize,transcript`. The `wav_filesize` (i.e. number of bytes) is used to group together audio of similar lengths for efficient batching.

## Collecting data

This PlayBook is focused on _training_ a speech recognition model, rather than on _collecting_ the data that is required for an accurate model. However, a good model starts with data.

* Ensure that your voice clips are 10-20 seconds in length. If they are longer or shorter than this, your model will be less accurate.

* Ensure that every character in your transcription of a voice clip is in your [alphabet.txt](ALPHABET.md) file

* Ensure that your voice clips exhibit the same sort of diversity you expect to encounter in your runtime audio. This means a diversity of accents, genders, background noise and so on.

* Ensure that your voice clips are created using similar microphones to that which you expect in your runtime audio. For example, if you expect to deploy your model on Android mobile phones, ensure that your training data is generated from Android mobile phones.

* Ensure that the phrasing on which your voice clips are generated covers the phrases you expect to encounter in your runtime audio.

### Punctuation and numbers

If you are collecting data that will be used to train a speech model, then you should remove punctuation marks such as dashes, tick marks, quote marks and so on. These will often be confused, and can hinder training an accurate model.

Numbers should be written in full (ie as a [cardinal](https://en.wikipedia.org/wiki/Cardinal_numeral)) - that is, as `eight` rather than `8`.

## Preparing your data for training

### Data from Common Voice

If you are using data from Common Voice for training a model, you will need to prepare it as [outlined in the 🐸STT documentation](https://stt.readthedocs.io/en/latest/COMMON_VOICE_DATA.html#common-voice-data).

In this example we will prepare the Indonesian dataset for training, but you can use any language from Common Voice that you prefer. We've chosen Indonesian as it has the same [orthographic alphabet](ALPHABET.md) as English, which means we don't have to use a different `alphabet.txt` file for training; we can use the default.

---
This example assumes you have already [set up a Docker [environment](ENVIRONMENT.md) for [training](TRAINING.md). If you have not yet set up your Docker environment, we suggest you pause here and do this first.
---

First, [download the dataset from Common Voice](https://commonvoice.mozilla.org/en/datasets), and extract the archive into your `stt-data` directory. This makes it available to your Docker container through a _bind mount_. Start your 🐸STT Docker container with the `stt-data` directory as a _bind mount_ (this is covered in the [environment](ENVIRONMENT.md) section).

Your CV corpus data should be available from within the Docker container.

 ```
 root@3de3afbe5d6f:/STT# ls  stt-data/cv-corpus-6.1-2020-12-11/id/
 clips    invalidated.tsv  reported.tsv  train.tsv
 dev.tsv  other.tsv        test.tsv      validated.tsv
```

The `ghcr.io/coqui-ai/stt-train` Docker image _does not_ come with `sox`, which is a package used for processing Common Voice data. We need to install `sox` first.

```
root@4b39be3b0ffc:/STT# apt-get -y update && apt-get install -y sox
```

Next, we will run the Common Voice importer that ships with 🐸STT.

```
root@3de3afbe5d6f:/STT# bin/import_cv2.py stt-data/cv-corpus-6.1-2020-12-11/id
```

This will process all the CV data into the `clips` directory, and it can now be used [for training](TRAINING.md).

## Importers

🐸STT ships with several scripts which act as _importers_ - preparing a corpus of data for training by 🐸STT.

If you want to create importers for a new language, or a new corpus, you will need to fork the 🐸STT repository, then add support for the new language and/or corpus by creating an _importer_ for that language/corpus.

The existing importer scripts are a good starting point for creating your own importers.

They are located in the `bin` directory of the 🐸STT repo:

```
root@3de3afbe5d6f:/STT# ls | grep import
import_aidatatang.py
import_aishell.py
import_ccpmf.py
import_cv.py
import_cv2.py
import_fisher.py
import_freestmandarin.py
import_gram_vaani.py
import_ldc93s1.py
import_librivox.py
import_lingua_libre.py
import_m-ailabs.py
import_magicdata.py
import_primewords.py
import_slr57.py
import_swb.py
import_swc.py
import_ted.py
import_timit.py
import_ts.py
import_tuda.py
import_vctk.py
import_voxforge.py
```

The importer scripts ensure that the `.wav` files and corresponding transcriptions are in the `.csv` format expected by 🐸STT.

---

[Home](README.md) | [Previous - About Coqui STT](ABOUT.md) | [Next - The alphabet.txt file](ALPHABET.md)
