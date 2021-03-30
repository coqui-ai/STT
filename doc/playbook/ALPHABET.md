[Home](README.md) | [Previous - Scorer - language model for determining which words occur together ](SCORER.md) | [Next - Acoustic Model and Language Model](AM_vs_LM.md)

# The alphabet.txt file

## Contents

- [The alphabet.txt file](#the-alphabettxt-file)
  * [Contents](#contents)
  * [What is alphabet.txt ?](#what-is-alphabettxt--)
  * [How does the Glue work?](#how-does-the-glue-work-)
    + [How to diagnose mis-matched alphabets?](#how-to-diagnose-mis-matched-alphabets-)
  * [Common alphabet.txt related errors](#common-alphabettxt-related-errors)

This tiny text file is easy to overlook, but it is very important. The *exact same* alphabet must be used to train the both acoustic model and the language model. This alphabet.txt is the glue that holds the language model and the acoustic model together.

## What is alphabet.txt ?

Let's take a look at the English [alphabet.txt](https://github.com/coqui-ai/STT/blob/master/data/alphabet.txt) which was used to train the release 🐸STT models. If you were to ask a native English speaker to write down the alphabet, this `alphabet.txt` isn't what they would write. *The `alphabet.txt` file contains all characters used in a language which are necessary for writing*. Looking at the English alphabet file, the first character is the space `" "`. We need spaces to separate words when writing. Following the space, we find all the familiar letters of the alphabet which children learn in school. Finally, we find the apostrophe "'". The apostrophe is needed for writing contractions, which are very common in English. The apostrophe can distinguish words like "we're" and "were", which have different prounuciations. Not all languages need spaces, and not all languages need apostrophes. Creating the alphabet for a new language takes some research. Two people creating the same alphabet file may disagree, and no one is objectively right. The best alphabet will depend on the target application and the available training data. You may notice that the `alphabet.txt` file released with 🐸STT for English does not contain any characters with accents, even though they do occur sometimes in English. The off-the-shelf 🐸STT model cannot produce words like "naïvely" or "résumé", and this was a design decision. We could make an alphabet that contains every possible character for every possible loan-word into English, but then we would need training data for all those new characters.

## How does the Glue work?

Quite simply, `alphabet.txt` helps 🐸STT make a lookup table, and at run-time that lookup table is used instead of characters themselves. For the English example, the 🐸STT acoustic model doesn't have any idea what the letter 'a' is, but it does know what index '1' is. The `alphabet.txt` file tells us that the index '1' for the acoustic model corresponds to the letter 'a', so we can make sense of the output. If the indeces for the acoustic model and language model don't match, then the acoustic model might hear an 'a', but the language model interprets it instead as 'b'. This mis-match is sneaky, and if the alphabets used for the acoustic model and language are similar, but slightly off, this is a hard problem to diagnose. If you used different `alphabet.txt` files, you may not get any run-time error messages, but the output transcriptions will make no sense.

### How to diagnose mis-matched alphabets?

If you think you used different alphabets to create a [language model and an acoustic model](AM_vs_LM.md), try decoding _without_ the scorer. If you can decode the audio without a scorer and the output is reasonable, but when you decode the same audio with a scorer, and the output is _not_ reasonable, then you could have mis-matched alphabets. Usually the easiest way to fix this is to re-compile the scorer with the correct alphabet.

[Read more information on building a language model (scorer)](SCORER.md).

## Common alphabet.txt related errors

One of the most common errors occurs when there is a character in the corpus that is not in the `alphabet.txt` file. You need to include the missing character in the `alphabet.txt` file.

```
File "/STT/training/coqui_stt_training/util/text.py", line 18, in text_to_char_array
  .format(transcript, context, list(ch for ch in transcript if not alphabet.CanEncodeSingle(ch))))
ValueError: Alphabet cannot encode transcript "panggil ambulan！" while processing sample "persistent-data/cv-corpus-6.1-2020-12-11/id/clips/common_voice_id_19338419.wav", check that your alphabet contains all characters in the training corpus. Missing characters are: ['！'].
```

---

[Home](README.md) | [Previous - Scorer - language model for determining which words occur together ](SCORER.md) | [Next - Acoustic Model and Language Model](AM_vs_LM.md)
