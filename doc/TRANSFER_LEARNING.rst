.. _transfer-learning:

Bootstrap from a pre-trained model
==================================

If you don't have thousands of hours of training data, you will probably find that bootstrapping from a pre-trained model is a critical step in training a production-ready STT model. Even in the case you do have thousands of hours of data, you will find that bootstrapping from a pre-trained model can significantly decrease training time. Unless you want to experiment with new neural architectures, you probably want to bootstrap from a pre-trained model.

There are currently two supported approaches to bootstrapping from a pre-trained 🐸STT model: fine-tuning or transfer-learning. Choosing which one to use depends on your target dataset. Does your data use the same alphabet as the release model? If "Yes", then you fine-tune. If "No", then you use transfer-learning.

If your own data uses the *extact* same alphabet as the English release model (i.e. ``a-z`` plus ``'``) then the release model's output layer will match your data, and you can just fine-tune the existing parameters. However, if you want to use a new alphabet (e.g. Cyrillic ``а``, ``б``, ``д``), the output layer of an English model will *not* match your data. In this case, you should use transfer-learning (i.e. reinitialize a new output layer that matches your target character set.

.. _training-fine-tuning:

Fine-Tuning (same alphabet)
---------------------------

You can fine-tune pre-trained model checkpoints by using the ``--checkpoint_dir`` flag. Specify the path to the checkpoints, and training will resume from the pre-trained model.

For example, if you want to fine tune existing checkpoints to your own data in ``my-train.csv``, ``my-dev.csv``, and ``my-test.csv``, you can do the following:

.. code-block:: bash

   $ python -m coqui_stt_training.train \
         --checkpoint_dir path/to/checkpoint/folder \
         --train_files my-train.csv \
         --dev_files my-dev.csv \
         --test_files my_test.csv

Transfer-Learning (new alphabet)
--------------------------------

If you want to bootstrap from an alphabet-based 🐸STT model but your text transcripts contain characters not found in the source model, then you will want to use transfer-learning instead of fine-tuning. If you want to bootstrap from a pre-trained UTF-8 ``byte output mode`` model - even if your data comes from a different language or uses a different alphabet - the model will be able to predict your new transcripts, and you should use fine-tuning instead.

🐸STT's transfer-learning allows you to remove certain layers from a pre-trained model, initialize new layers for your target data, stitch together the old and new layers, and update all layers via gradient descent. Transfer-learning always removes the output layer of the pre-trained model in order to fit your new target alphabet. The simplest case of transfer-learning is when you only remove the output layer.

In 🐸STT's implementation of transfer-learning, all removed layers must be contiguous and include the output layer. The flag to control the number of layers you remove from the source model is ``--drop_source_layers``. This flag accepts an integer from ``1`` to ``5``, specifying how many layers to remove from the pre-trained model. For example, with ``--drop_source_layers 3`` and a 🐸STT off-the-shelf model, you will drop the last three layers of the model: the output layer, penultimate layer, and LSTM layer. All dropped layers will be reinintialized, and (crucially) the output layer will be defined to match your supplied target alphabet.

You need to specify the location of the pre-trained model with ``--load_checkpoint_dir`` and define where your new model checkpoints will be saved with ``--save_checkpoint_dir``. You need to specify how many layers to remove (aka "drop") from the pre-trained model: ``--drop_source_layers``. You also need to supply your new alphabet file using the standard ``--alphabet_config_path`` (remember, using a new alphabet is the whole reason you want to use transfer-learning).

.. code-block:: bash

       python -m coqui_stt_training.train \
           --drop_source_layers 1 \
           --alphabet_config_path my-alphabet.txt \
           --save_checkpoint_dir path/to/output-checkpoint/folder \
           --load_checkpoint_dir path/to/input-checkpoint/folder \
           --train_files my-new-language-train.csv \
           --dev_files   my-new-language-dev.csv \
           --test_files  my-new-language-test.csv

Bootstrapping from Coqui STT release checkpoints
------------------------------------------------

Currently, 🐸STT release models are trained with ``--n_hidden 2048``, so you need to use that same value when initializing from the release models. Release models are also trained with ``--train_cudnn``, so you'll need to specify that as well. If you don't have a CUDA compatible GPU, then you can workaround it by using the ``--load_cudnn`` flag.

You cannot use ``--automatic_mixed_precision`` when loading release checkpoints, as they do not use automatic mixed precision training.

If you try to load a release model without following these steps, you may experience run-time errors.
