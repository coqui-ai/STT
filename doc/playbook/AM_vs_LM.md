[Home](README.md) | [Previous - Scorer - language model for determining which words occur together](SCORER.md) | [Next - Setting up your Coqui STT training environment](ENVIRONMENT.md)

# Acoustic model vs. Language model

## Contents

- [Acoustic model vs. Language model](#acoustic-model-vs-language-model)
  * [Contents](#contents)
  * [Training](#training)

At runtime, 🐸STT is made up of two main parts: (1) the acoustic model and (2) the language model. The acoustic model takes audio as input and converts it to a probability over characters in the alphabet. The language model helps to turn these probabilities into words of coherent language. The language model (aka. the scorer), assigns probabilities to words and phrases based on statistics from training data. The language model knows that "I read a book" is much more probable then "I red a book", even though they may sound identical to the acoustic model.

## Training

<<<<<<< HEAD
The acoustic model is a neural network trained with Tensorflow, and the training data is a corpus of speech and transcripts.

The language model is a n-gram model trained with kenlm, and the training data is a corpus of text.
=======
<<<<<<< HEAD
The acoustic model is a neural network trained with Tensorflow, and the training data is a corpus of speech and transcripts.

The language model is a n-gram model trained with kenlm, and the training data is a corpus of text.
=======
The acoustic model is a neural network trained with TensorFlow, and the training data is a corpus of speech and transcripts.

The language model is a n-gram model trained with KenLM, and the training data is a corpus of text.
>>>>>>> coqui-ai-main
>>>>>>> 94b13b64c30dd1349c6e325dba22877620ef914b

---

[Home](README.md) | [Previous - Scorer - language model for determining which words occur together](SCORER.md) | [Next - Setting up your Coqui STT training environment](ENVIRONMENT.md)
