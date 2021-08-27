.. _common-voice-data:

Common Voice training data
==========================

This document gives some information about using Common Voice data with STT. If you're in need of training data, the Common Voice corpus is a good place to start.

Common Voice consists of voice data that was donated through Mozilla's `Common Voice <https://commonvoice.mozilla.org/>`_ initiative. You can download the data sets for various languages `here <https://commonvoice.mozilla.org/data>`_.

After you download and extract a data set for one language, you'll find the following contents:

* ``.tsv`` files, containing metadata such as text transcripts
* ``.mp3`` audio files, located in the ``clips`` directory

🐸STT cannot directly work with Common Voice data, so you should run our importer script ``bin/import_cv2.py`` to format the data correctly:

.. code-block:: bash

   bin/import_cv2.py --filter_alphabet path/to/some/alphabet.txt /path/to/extracted/common-voice/archive

Providing a filter alphabet is optional. This alphabet is used to exclude all audio files whose transcripts contain characters not in the specified alphabet. Running the importer with ``-h`` will show you additional options.

The importer will create a new ``WAV`` file for every ``MP3`` file in the ``clips`` directory. The importer will also create the following ``CSV`` files:

* ``clips/train.csv``
* ``clips/dev.csv``
* ``clips/test.csv``

The CSV files contain the following fields:

* ``wav_filename`` - path to the audio file, may be absolute or relative. Our importer produces relative paths
* ``wav_filesize`` - samples size given in bytes, used for sorting the data before training. Expects integer
* ``transcript`` - transcription target for the sample

To use Common Voice data for training, validation and testing, you should pass the ``CSV`` filenames via ``--train_files``, ``--dev_files``, ``--test_files``.

For example, if you download, extracted, and imported the French language data from Common Voice, you will have a new local directory named ``fr``. You can train STT with this new French data as such:

.. code-block:: bash

   $ python -m coqui_stt_training.train \
         --train_files fr/clips/train.csv \
         --dev_files fr/clips/dev.csv \
         --test_files fr/clips/test.csv
