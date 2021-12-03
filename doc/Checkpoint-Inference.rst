.. _checkpoint-inference:

Inference tools in the training package
=======================================

The standard deployment options for 🐸STT use highly optimized packages for deployment in real time, single-stream, low latency use cases. They take as input exported models which are also optimized, leading to further space and runtime gains. On the other hand, for the development of new features, it might be easier to use the training code for prototyping, which will allow you to test your changes without needing to recompile source code.

The training package contains options for performing inference directly from a checkpoint (and optionally a scorer), without needing to export a model. They are documented below, and all require a working :ref:`training environment <intro-training-docs>` before they can be used. Additionally, they require the Python ``webrtcvad`` package to be installed. This can either be done by specifying the "transcribe" extra when installing the training package, or by installing it manually in your training environment:

.. code-block:: bash

   $ python -m pip install webrtcvad

Note that if your goal is to evaluate a trained model and obtain accuracy metrics, you should use the evaluation module: ``python -m coqui_stt_training.evaluate``, which calculates character and word error rates, from a properly formatted CSV file (specified with the ``--test_files`` flag. See the :ref:`training docs <intro-training-docs>` for more information).

Single file (aka one-shot) inference
------------------------------------

This is the simplest way to perform inference from a checkpoint. It takes a single WAV file as input with the ``--one_shot_infer`` flag, and outputs the predicted transcription for that file.

.. code-block:: bash

   $ python -m coqui_stt_training.training_graph_inference --checkpoint_dir coqui-stt-1.0.0-checkpoint --scorer_path huge-vocabulary.scorer --n_hidden 2048 --one_shot_infer audio/2830-3980-0043.wav
   I --alphabet_config_path not specified, but found an alphabet file alongside specified checkpoint (coqui-stt-1.0.0-checkpoint/alphabet.txt). Will use this alphabet file for this run.
   I Loading best validating checkpoint from coqui-stt-1.0.0-checkpoint/best_dev-3663881
   I Loading variable from checkpoint: cudnn_lstm/rnn/multi_rnn_cell/cell_0/cudnn_compatible_lstm_cell/bias
   I Loading variable from checkpoint: cudnn_lstm/rnn/multi_rnn_cell/cell_0/cudnn_compatible_lstm_cell/kernel
   I Loading variable from checkpoint: layer_1/bias
   I Loading variable from checkpoint: layer_1/weights
   I Loading variable from checkpoint: layer_2/bias
   I Loading variable from checkpoint: layer_2/weights
   I Loading variable from checkpoint: layer_3/bias
   I Loading variable from checkpoint: layer_3/weights
   I Loading variable from checkpoint: layer_5/bias
   I Loading variable from checkpoint: layer_5/weights
   I Loading variable from checkpoint: layer_6/bias
   I Loading variable from checkpoint: layer_6/weights
   experience proves this

Transcription of longer audio files
-----------------------------------

If you have longer audio files to transcribe, we offer a script which uses Voice Activity Detection (VAD) to split audio files in chunks and perform batched inference on said files. This can speed-up the transcription time significantly. The transcription script will also output the results in JSON format, allowing for easier programmatic usage of the outputs.

There are two main usage modes: transcribing a single file, or scanning a directory for audio files and transcribing all of them.

Transcribing a single file
^^^^^^^^^^^^^^^^^^^^^^^^^^

For a single audio file, you can specify it directly in the ``--src`` flag of the ``python -m coqui_stt_training.transcribe`` script:

.. code-block:: bash

   $ python -m coqui_stt_training.transcribe --checkpoint_dir coqui-stt-1.0.0-checkpoint --n_hidden 2048 --scorer_path huge-vocabulary.scorer --vad_aggressiveness 0 --src audio/2830-3980-0043.wav
   [1]: "audio/2830-3980-0043.wav" -> "audio/2830-3980-0043.tlog"
   Transcribing files: 100%|███████████████████████████████████| 1/1 [00:05<00:00,  5.40s/it]
   $ cat audio/2830-3980-0043.tlog
   [{"start": 150, "end": 1950, "transcript": "experience proves this"}]

Note the use of the ``--vad_aggressiveness`` flag above to control the behavior of the VAD process used to find silent sections of the audio file for splitting into chunks. You can run ``python -m coqui_stt_training.transcribe --help`` to see the full listing of options, the last ones are specific to the transcribe module.

By default the transcription results are put in a ``.tlog`` file next to the audio file that was transcribed, but you can specify a different location with the ``--dst path/to/some/file.tlog`` flag. This only works when trancribing a single file.

Scanning a directory for audio files
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Alternatively you can also specify a directory in the ``--src`` flag, in which case the directory will be scanned for any WAV files to be transcribed. If you specify ``--recursive true``, it'll scan the directory recursively, going into any subdirectories as well. Transcription results will be placed in a ``.tlog`` file alongside every audio file that was found by the process.

Multiple processes will be used to distribute the transcription work among available CPUs.

.. code-block:: bash

   $ python -m coqui_stt_training.transcribe --checkpoint_dir coqui-stt-1.0.0-checkpoint --n_hidden 2048 --scorer_path huge-vocabulary.scorer --vad_aggressiveness 0 --src audio/ --recursive true
   Transcribing all files in --src directory audio
   Transcribing files:   0%|                                           | 0/3 [00:00<?, ?it/s]
   [3]: "audio/8455-210777-0068.wav" -> "audio/8455-210777-0068.tlog"
   [1]: "audio/2830-3980-0043.wav" -> "audio/2830-3980-0043.tlog"
   [2]: "audio/4507-16021-0012.wav" -> "audio/4507-16021-0012.tlog"
   Transcribing files: 100%|███████████████████████████████████| 3/3 [00:07<00:00,  2.50s/it]
