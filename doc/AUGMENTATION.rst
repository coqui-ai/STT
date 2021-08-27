.. _training-data-augmentation:

Training Data Augmentation
==========================

This document is an overview of the augmentation techniques available for training with STT.

Training data augmentations can help STT models better transcribe new speech at deployment time. The basic intuition behind data augmentation is the following: by distorting, modifying, or adding to your existing audio data, you can create a training set many times larger than what you started with. If you use a larger training data set to train as STT model, you force the model to learn more generalizable characteristics of speech, making `overfitting <https://en.wikipedia.org/wiki/Overfitting>`_ more difficult. If you can't find a larger data set of speech, you can create one with data augmentation.

We have implemented a pre-processing pipeline with various augmentation techniques on audio data (i.e. raw ``PCM`` and spectrograms).

Each audio file in your training data will be potentially affected by the sequence of augmentations you specify. Whether or not an augmentation will *actually* get applied to a given audio file is determined by the augmentation's probability value. For example, a probability value of ``p=0.1`` means the according augmentation has a 10% chance of being applied to a given audio file. This also means that augmentations are not mutually exclusive on a per-audio-file basis.

The ``--augment`` flag uses a common syntax for all augmentation types:

.. code-block::

  --augment augmentation_type1[param1=value1,param2=value2,...] --augment augmentation_type2[param1=value1,param2=value2,...] ...

For example, for the ``overlay`` augmentation:

.. code-block::

  python -m coqui_stt_training.train --augment "overlay[p=0.1,source=/path/to/audio.sdb,snr=20.0]" ...

In the documentation below, whenever a value is specified as ``<float-range>`` or ``<int-range>``, it supports one of the follow formats:

  * ``<value>``: A constant (int or float) value.

  * ``<value>~<r>``: A center value with a randomization radius around it. E.g. ``1.2~0.4`` will result in picking of a uniformly random value between 0.8 and 1.6 on each sample augmentation.

  * ``<start>:<end>``: The value will range from `<start>` at the beginning of the training to `<end>` at the end of the training. E.g. ``-0.2:1.2`` (float) or ``2000:4000`` (int)

  * ``<start>:<end>~<r>``: Combination of the two previous cases with a ranging center value. E.g. ``4-6~2`` would at the beginning of the training pick values between 2 and 6 and at the end of the training between 4 and 8.

Ranges specified with integer limits will only assume integer (rounded) values.

.. warning::
    When feature caching is enabled, by default the cache has no expiration limit and will be used for the entire training run. This will cause these augmentations to only be performed once during the first epoch and the result will be reused for subsequent epochs. This would not only hinder value ranges from reaching their intended final values, but could also lead to unintended over-fitting. In this case flag ``--cache_for_epochs N`` (with N > 1) should be used to periodically invalidate the cache after every N epochs and thus allow samples to be re-augmented in new ways and with current range-values.

Every augmentation targets a certain representation of the sample - in this documentation these representations are referred to as *domains*.
Augmentations are applied in the following order:

1. **sample** domain: The sample just got loaded and its waveform is represented as a NumPy array. For implementation reasons these augmentations are the only ones that can be "simulated" through ``bin/play.py``.

2. **signal** domain: The sample waveform is represented as a tensor.

3. **spectrogram** domain: The sample spectrogram is represented as a tensor.

4. **features** domain: The sample's mel spectrogram features are represented as a tensor.

Within a single domain, augmentations are applied in the same order as they appear in the command-line.


Sample domain augmentations
---------------------------

**Overlay augmentation** ``--augment "overlay[p=<float>,source=<str>,snr=<float-range>,layers=<int-range>]"``
  Layers another audio source (multiple times) onto augmented samples.

  * **p**: probability value between 0.0 (never) and 1.0 (always) if a given sample gets augmented by this method

  * **source**: path to the sample collection to use for augmenting (\*.sdb or \*.csv file). It will be repeated if there are not enough samples left.

  * **snr**: signal to noise ratio in dB - positive values for lowering volume of the overlay in relation to the sample

  * **layers**: number of layers added onto the sample (e.g. 10 layers of speech to get "cocktail-party effect"). A layer is just a sample of the same duration as the sample to augment. It gets stitched together from as many source samples as required.


**Reverb augmentation** ``--augment "reverb[p=<float>,delay=<float-range>,decay=<float-range>]"``
  Adds simplified (no all-pass filters) `Schroeder reverberation <https://ccrma.stanford.edu/~jos/pasp/Schroeder_Reverberators.html>`_ to the augmented samples.

  * **p**: probability value between 0.0 (never) and 1.0 (always) if a given sample gets augmented by this method

  * **delay**: time delay in ms for the first signal reflection - higher values are widening the perceived "room"

  * **decay**: sound decay in dB per reflection - higher values will result in a less reflective perceived "room"


**Resample augmentation** ``--augment "resample[p=<float>,rate=<int-range>]"``
  Resamples augmented samples to another sample rate and then resamples back to the original sample rate.

  * **p**: probability value between 0.0 (never) and 1.0 (always) if a given sample gets augmented by this method

  * **rate**: sample-rate to re-sample to


**Codec augmentation** ``--augment "codec[p=<float>,bitrate=<int-range>]"``
  Compresses and then decompresses augmented samples using the lossy Opus audio codec.

  * **p**: probability value between 0.0 (never) and 1.0 (always) if a given sample gets augmented by this method

  * **bitrate**: bitrate used during compression


**Volume augmentation** ``--augment "volume[p=<float>,dbfs=<float-range>]"``
  Measures and levels augmented samples to a target dBFS value.

  * **p**: probability value between 0.0 (never) and 1.0 (always) if a given sample gets augmented by this method

  * **dbfs** : target volume in dBFS (default value of 3.0103 will normalize min and max amplitudes to -1.0/1.0)

Spectrogram domain augmentations
--------------------------------

**Pitch augmentation** ``--augment "pitch[p=<float>,pitch=<float-range>]"``
  Scales spectrogram on frequency axis and thus changes pitch.

  * **p**: probability value between 0.0 (never) and 1.0 (always) if a given sample gets augmented by this method

  * **pitch**: pitch factor by with the frequency axis is scaled (e.g. a value of 2.0 will raise audio frequency by one octave)


**Tempo augmentation** ``--augment "tempo[p=<float>,factor=<float-range>]"``
  Scales spectrogram on time axis and thus changes playback tempo.

  * **p**: probability value between 0.0 (never) and 1.0 (always) if a given sample gets augmented by this method

  * **factor**: speed factor by which the time axis is stretched or shrunken (e.g. a value of 2.0 will double playback tempo)


**Warp augmentation** ``--augment "warp[p=<float>,nt=<int-range>,nf=<int-range>,wt=<float-range>,wf=<float-range>]"``
  Applies a non-linear image warp to the spectrogram. This is achieved by randomly shifting a grid of equally distributed warp points along time and frequency axis.

  * **p**: probability value between 0.0 (never) and 1.0 (always) if a given sample gets augmented by this method

  * **nt**: number of equally distributed warp grid lines along time axis of the spectrogram (excluding the edges)

  * **nf**: number of equally distributed warp grid lines along frequency axis of the spectrogram (excluding the edges)

  * **wt**: standard deviation of the random shift applied to warp points along time axis (0.0 = no warp, 1.0 = half the distance to the neighbour point)

  * **wf**: standard deviation of the random shift applied to warp points along frequency axis (0.0 = no warp, 1.0 = half the distance to the neighbour point)


**Frequency mask augmentation** ``--augment "frequency_mask[p=<float>,n=<int-range>,size=<int-range>]"``
  Sets frequency-intervals within the augmented samples to zero (silence) at random frequencies. See the SpecAugment paper for more details - https://arxiv.org/abs/1904.08779

  * **p**: probability value between 0.0 (never) and 1.0 (always) if a given sample gets augmented by this method

  * **n**: number of intervals to mask

  * **size**: number of frequency bands to mask per interval

Multi domain augmentations
--------------------------

**Time mask augmentation** ``--augment "time_mask[p=<float>,n=<int-range>,size=<float-range>,domain=<domain>]"``
  Sets time-intervals within the augmented samples to zero (silence) at random positions.

  * **p**: probability value between 0.0 (never) and 1.0 (always) if a given sample gets augmented by this method

  * **n**: number of intervals to set to zero

  * **size**: duration of intervals in ms

  * **domain**: data representation to apply augmentation to - "signal", "features" or "spectrogram" (default)


**Dropout augmentation** ``--augment "dropout[p=<float>,rate=<float-range>,domain=<domain>]"``
  Zeros random data points of the targeted data representation.

  * **p**: probability value between 0.0 (never) and 1.0 (always) if a given sample gets augmented by this method

  * **rate**: dropout rate ranging from 0.0 for no dropout to 1.0 for 100% dropout

  * **domain**: data representation to apply augmentation to - "signal", "features" or "spectrogram" (default)


**Add augmentation** ``--augment "add[p=<float>,stddev=<float-range>,domain=<domain>]"``
  Adds random values picked from a normal distribution (with a mean of 0.0) to all data points of the targeted data representation.

  * **p**: probability value between 0.0 (never) and 1.0 (always) if a given sample gets augmented by this method

  * **stddev**: standard deviation of the normal distribution to pick values from

  * **domain**: data representation to apply augmentation to - "signal", "features" (default) or "spectrogram"


**Multiply augmentation** ``--augment "multiply[p=<float>,stddev=<float-range>,domain=<domain>]"``
  Multiplies all data points of the targeted data representation with random values picked from a normal distribution (with a mean of 1.0).

  * **p**: probability value between 0.0 (never) and 1.0 (always) if a given sample gets augmented by this method

  * **stddev**: standard deviation of the normal distribution to pick values from

  * **domain**: data representation to apply augmentation to - "signal", "features" (default) or "spectrogram"


Example training with all augmentations:

.. code-block:: bash

        python -m coqui_stt_training.train \
          --train_files "train.sdb" \
          --epochs 100 \
          --augment "overlay[p=0.5,source=noise.sdb,layers=1,snr=50:20~10]" \
          --augment "reverb[p=0.1,delay=50.0~30.0,decay=10.0:2.0~1.0]" \
          --augment "resample[p=0.1,rate=12000:8000~4000]" \
          --augment "codec[p=0.1,bitrate=48000:16000]" \
          --augment "volume[p=0.1,dbfs=-10:-40]" \
          --augment "pitch[p=0.1,pitch=1~0.2]" \
          --augment "tempo[p=0.1,factor=1~0.5]" \
          --augment "warp[p=0.1,nt=4,nf=1,wt=0.5:1.0,wf=0.1:0.2]" \
          --augment "frequency_mask[p=0.1,n=1:3,size=1:5]" \
          --augment "time_mask[p=0.1,domain=signal,n=3:10~2,size=50:100~40]" \
          --augment "dropout[p=0.1,rate=0.05]" \
          --augment "add[p=0.1,domain=signal,stddev=0~0.5]" \
          --augment "multiply[p=0.1,domain=features,stddev=0~0.5]" \
          [...]


The ``bin/play.py`` and ``bin/data_set_tool.py`` tools also support ``--augment`` parameters (for sample domain augmentations) and can be used for experimenting with different configurations or creating augmented data sets.

Example of playing all samples with reverberation and maximized volume:

.. code-block:: bash

        bin/play.py --augment "reverb[p=0.1,delay=50.0,decay=2.0]" --augment volume --random test.sdb

Example simulation of the codec augmentation of a wav-file first at the beginning and then at the end of an epoch:

.. code-block:: bash

        bin/play.py --augment "codec[p=0.1,bitrate=48000:16000]" --clock 0.0 test.wav
        bin/play.py --augment "codec[p=0.1,bitrate=48000:16000]" --clock 1.0 test.wav

Example of creating a pre-augmented test set:

.. code-block:: bash

        bin/data_set_tool.py \
          --augment "overlay[source=noise.sdb,layers=1,snr=20~10]" \
          --augment "resample[rate=12000:8000~4000]" \
          test.sdb test-augmented.sdb
