[Home](README.md) | [Previous - Setting up your Coqui STT training environment](ENVIRONMENT.md) | [Next - Testing and evaluating your trained model](TESTING.md)

# Training a Coqui STT model

## Contents

- [Training a Coqui STT model](#training-a-coqui-stt-model)
  * [Contents](#contents)
  * [Making training files available to the Docker container](#making-training-files-available-to-the-docker-container)
  * [Running training](#running-training)
    + [Specifying checkpoint directories so that you can restart training from a checkpoint](#specifying-checkpoint-directories-so-that-you-can-restart-training-from-a-checkpoint)
      - [Advanced checkpoint configuration](#advanced-checkpoint-configuration)
        * [How checkpoints are stored](#how-checkpoints-are-stored)
        * [Managing disk space and checkpoints](#managing-disk-space-and-checkpoints)
        * [Different checkpoints for loading and saving](#different-checkpoints-for-loading-and-saving)
    + [Specifying the directory that the trained model should be exported to](#specifying-the-directory-that-the-trained-model-should-be-exported-to)
  * [Other useful parameters that can be passed to `train.py`](#other-useful-parameters-that-can-be-passed-to--trainpy-)
    + [`n_hidden` parameter](#-n-hidden--parameter)
    + [Reduce learning rate on plateau (RLROP)](#reduce-learning-rate-on-plateau--rlrop-)
    + [Early stopping](#early-stopping)
    + [Dropout rate](#dropout-rate)
  * [Steps and epochs](#steps-and-epochs)
  * [Advanced training options](#advanced-training-options)
  * [Monitoring GPU use with `nvtop`](#monitoring-gpu-use-with--nvtop-)
  * [Possible errors](#possible-errors)
    + [`Failed to get convolution algorithm. This is probably because cuDNN failed to initialize, so try looking to see if a warning log message was printed above.` error when training](#-failed-to-get-convolution-algorithm-this-is-probably-because-cudnn-failed-to-initialize--so-try-looking-to-see-if-a-warning-log-message-was-printed-above--error-when-training)

## Making training files available to the Docker container

Before we can train a model, we need to make the training data available to the Docker container. The training data was previously prepared in the [instructions for formatting data](DATA_FORMATTING.md). Copy or extract them to the directory you specified in your _bind mount_. This will make them available to the Docker container.

```
$ cd stt-data
$ ls cv-corpus-6.1-2020-12-11/
total 12
4 drwxr-xr-x 3 kathyreid kathyreid 4096 Feb  9 10:42 ./
4 drwxrwxr-x 7 kathyreid kathyreid 4096 Feb  9 10:43 ../
4 drwxr-xr-x 3 kathyreid kathyreid 4096 Feb  9 10:43 id/
```

We're now ready to being training.

## Running training

We're going to walk through some of the key parameters you can use with `train.py`.

```
python3 train.py \
  --train_files persistent-data/cv-corpus-6.1-2020-12-11/id/clips/train.csv \
  --dev_files persistent-data/cv-corpus-6.1-2020-12-11/id/clips/dev.csv \
  --test_files persistent-data/cv-corpus-6.1-2020-12-11/id/clips/test.csv
```

**Do not run this yet**

The options `--train_files`, `--dev_files` and `--test_files` take a path to the relevant data, which was prepared in the section on [data formatting](DATA_FORMATTING.md).

### Specifying checkpoint directories so that you can restart training from a checkpoint

As you are training your model, 🐸STT will store _checkpoints_ to disk. The checkpoint allows interruption to training, and to restart training from the checkpoint, saving hours of training time.

Because we have our [training environment](ENVIRONMENT.md) configured to use Docker, we must ensure that our checkpoint directories are stored in the directory used by the _bind mount_, so that they _persist_ in the event of failure.

To specify checkpoint directories, use the `--checkpoint_dir` parameter with `train.py`:

```
python3 train.py \
  --train_files stt-data/cv-corpus-6.1-2020-12-11/id/clips/train.csv \
  --dev_files stt-data/cv-corpus-6.1-2020-12-11/id/clips/dev.csv \
  --test_files stt-data/cv-corpus-6.1-2020-12-11/id/clips/test.csv \
  --checkpoint_dir stt-data/checkpoints
```

**Do not run this yet**

#### Advanced checkpoint configuration

##### How checkpoints are stored

_Checkpoints_ are stored as [Tensorflow `tf.Variable` objects](https://www.tensorflow.org/guide/checkpoint). This is a binary file format; that is, you won't be able to read it with a text editor. The _checkpoint_ stores all the weights and biases of the current state of the _neural network_ as training progresses.

_Checkpoints_ are named by the total number of steps completed. For example, if you train for 100 epochs at 2000 steps per epoch, then the final _checkpoint_ will be named `200000`.

```
~/stt-data/checkpoints-true-id$ ls
total 1053716
     4 drwxr-xr-x 2 root      root           4096 Feb 24 14:17 ./
     4 drwxrwxr-x 5 root      root      4096 Feb 24 13:18 ../
174376 -rw-r--r-- 1 root      root      178557296 Feb 24 14:11 best_dev-12774.data-00000-of-00001
     4 -rw-r--r-- 1 root      root           1469 Feb 24 14:11 best_dev-12774.index
  1236 -rw-r--r-- 1 root      root        1262944 Feb 24 14:11 best_dev-12774.meta
     4 -rw-r--r-- 1 root      root             85 Feb 24 14:11 best_dev_checkpoint
     4 -rw-r--r-- 1 root      root            247 Feb 24 14:17 checkpoint
     4 -rw-r--r-- 1 root      root           3888 Feb 24 13:18 flags.txt
174376 -rw-r--r-- 1 root      root      178557296 Feb 24 14:09 train-12774.data-00000-of-00001
     4 -rw-r--r-- 1 root      root           1469 Feb 24 14:09 train-12774.index
  1236 -rw-r--r-- 1 root      root        1262938 Feb 24 14:09 train-12774.meta
174376 -rw-r--r-- 1 root      root      178557296 Feb 24 14:13 train-14903.data-00000-of-00001
     4 -rw-r--r-- 1 root      root           1469 Feb 24 14:13 train-14903.index
  1236 -rw-r--r-- 1 root      root        1262938 Feb 24 14:13 train-14903.meta
174376 -rw-r--r-- 1 root      root      178557296 Feb 24 14:17 train-17032.data-00000-of-00001
     4 -rw-r--r-- 1 root      root           1469 Feb 24 14:17 train-17032.index
  1236 -rw-r--r-- 1 root      root        1262938 Feb 24 14:17 train-17032.meta
174376 -rw-r--r-- 1 root      root      178557296 Feb 24 14:01 train-19161.data-00000-of-00001
     4 -rw-r--r-- 1 root      root           1469 Feb 24 14:01 train-19161.index
  1236 -rw-r--r-- 1 root      root        1262938 Feb 24 14:01 train-19161.meta
174376 -rw-r--r-- 1 root      root      178557296 Feb 24 14:05 train-21290.data-00000-of-00001
     4 -rw-r--r-- 1 root      root           1469 Feb 24 14:05 train-21290.index
```

##### Managing disk space and checkpoints

_Checkpoints_ can consume a lot of disk space, so you may wish to configure how often a _checkpoint_ is written to disk, and how many _checkpoints_ are stored.

* `--checkpoint_secs` specifies the time interval for storing a _checkpoint_. The default is `600`, or every five minutes. You may wish to increase this if you have limited disk space.

* `--max_to_keep` specifies how many _checkpoints_ to keep. The default is `5`. You may wish to decrease this if you have limited disk space.

In this example we will store a _checkpoint_ every 15 minutes, and keep only 3 _checkpoints_.

```
python3 train.py \
  --train_files stt-data/cv-corpus-6.1-2020-12-11/id/clips/train.csv \
  --dev_files stt-data/cv-corpus-6.1-2020-12-11/id/clips/dev.csv \
  --test_files stt-data/cv-corpus-6.1-2020-12-11/id/clips/test.csv \
  --checkpoint_dir stt-data/checkpoints \
  --checkpoint_secs 1800 \
  --max_to_keep 3
```

**Do not run this yet**

##### Different checkpoints for loading and saving

In some cases, you may wish to _load_ _checkpoints_ from one location, but _save_ _checkpoints_ to another location - for example if you are doing fine tuning or transfer learning.

* `--load_checkpoint_dir` specifies the directory to load _checkpoints_ from.

* `--save_checkpoint_dir` specifies the directory to save _checkpoints_ to.

In this example we will store a _checkpoint_ every 15 minutes, and keep only 3 _checkpoints_.

```
python3 train.py \
  --train_files stt-data/cv-corpus-6.1-2020-12-11/id/clips/train.csv \
  --dev_files stt-data/cv-corpus-6.1-2020-12-11/id/clips/dev.csv \
  --test_files stt-data/cv-corpus-6.1-2020-12-11/id/clips/test.csv \
  --load_checkpoint_dir stt-data/checkpoints-to-train-from \
  --save_checkpoint_dir stt-data/checkpoints-to-save-to
```

**Do not run this yet**

### Specifying the directory that the trained model should be exported to

Again, because we have our [training environment](ENVIRONMENT.md) configured to use Docker, we must ensure that our trained model is stored in the directory used by the _bind mount_, so that it _persists_ in the event of failure of the Docker container.

To specify where the trained model should be saved, use the `--export-dir` parameter with `train.py`:

```
python3 train.py \
  --train_files stt-data/cv-corpus-6.1-2020-12-11/id/clips/train.csv \
  --dev_files stt-data/cv-corpus-6.1-2020-12-11/id/clips/dev.csv \
  --test_files stt-data/cv-corpus-6.1-2020-12-11/id/clips/test.csv \
  --checkpoint_dir stt-data/checkpoints \
  --export_dir stt-data/exported-model
```

**You can run this command to start training**

## Other useful parameters that can be passed to `train.py`

_For a full list of parameters that can be passed to `train.py`, please [consult the documentation](https://stt.readthedocs.io/en/latest/Flags.html#training-flags)._

`train.py` has many parameters - too many to cover in an introductory PlayBook. Here are some of the commonly used parameters that are useful to explore as you begin to train speech recognition models with 🐸STT.

### `n_hidden` parameter

Neural networks work through a series of _layers_. Usually there is an _input layer_, which takes an input - in this case an audio recording, and a series of _hidden layers_ which identify features of the _input layer_, and an _output layer_, which makes a prediction - in this case a character.

In large datasets, you need many _hidden layers_ to arrive at an accurate trained model. With smaller datasets, often called _toy corpora_ or _toy datasets_, you don't need as many _hidden layers_.

If you are learning how to train using 🐸STT, and are working with a small dataset, you will save time by reducing the value of `--n_hidden`. This reduces the number of _hidden layers_ in the neural network. This both reduces the amount of computing resources consumed during training, and makes training a model much faster.

The `--n_hidden` parameter has a default value of `2048`.

```
python3 train.py \
  --train_files stt-data/cv-corpus-6.1-2020-12-11/id/clips/train.csv \
  --dev_files stt-data/cv-corpus-6.1-2020-12-11/id/clips/dev.csv \
  --test_files stt-data/cv-corpus-6.1-2020-12-11/id/clips/test.csv \
  --checkpoint_dir stt-data/checkpoints \
  --export_dir stt-data/exported-model \
  --n_hidden 64
```

### Reduce learning rate on plateau (RLROP)

In neural networks, the _learning rate_ is the rate at which the neural network makes adjustments to the predictions it generates. The accuracy of predictions is measured using the _loss_. The lower the _loss_, the lower the difference between the neural network's predictions, and actual known values. If training is effective, _loss_ will reduce over time. A neural network that has a _loss_ of `0` has perfect prediction.

 If the _learning rate_ is too low, predictions will take a long time to align with actual targets. If the learning rate is too high, predictions will overshoot actual targets. The _learning rate_ has to aim for a balance between _exploration and exploitation_.

If loss is not reducing over time, then the training is said to have _plateaued_ - that is, the adjustments to the predictions are not reducing _loss_. By adjusting the _learning rate_, and other parameters, we may escape the _plateau_ and continue to decrease _loss_.

* The `--reduce_lr_on_plateau` parameter instructs `train.py` to automatically reduce the _learning rate_ if a _plateau_ is detected. By default, this is `false`.

* The `--plateau_epochs` parameter specifies the number of epochs of training during which there is no reduction in loss that should be considered a _plateau_. The default value is `10`.

* The `--plateau_reduction` parameter specifies a multiplicative factor that is applied to the current learning rate if a _plateau_ is detected. This number **must** be less than `1`, otherwise it will _increase_ the learning rate. The default value is `0.1`.

An example of training with these parameters would be:

```
python3 train.py \
  --train_files stt-data/cv-corpus-6.1-2020-12-11/id/clips/train.csv \
  --dev_files stt-data/cv-corpus-6.1-2020-12-11/id/clips/dev.csv \
  --test_files stt-data/cv-corpus-6.1-2020-12-11/id/clips/test.csv \
  --checkpoint_dir stt-data/checkpoints \
  --export_dir stt-data/exported-model \
  --n_hidden 64 \
  --reduce_lr_on_plateau true \
  --plateau_epochs 8 \
  --plateau_reduction 0.08
```

### Early stopping

If training is not resulting in a reduction of _loss_ over time, you can pass parameters to `train.py` that will stop training. This is called _early stopping_ and is useful if you are using cloud compute resources, or shared resources, and can't monitor the training continuously.

* The `--early_stop` parameter enables early stopping. It is set to `false` by default.

* The `--es_epochs` parameter takes an integer of the number of epochs with no improvement after which training will be stopped. It is set to `25` by default, for example if this parameter is omitted, but `--early_stop` is set to `true`.

* The `--es_min_delta` parameter is the minimum change in _loss_ per epoch that qualifies as an improvement. By default it is set to `0.05`.

An example of training with these parameters would be:

```
python3 train.py \
  --train_files stt-data/cv-corpus-6.1-2020-12-11/id/clips/train.csv \
  --dev_files stt-data/cv-corpus-6.1-2020-12-11/id/clips/dev.csv \
  --test_files stt-data/cv-corpus-6.1-2020-12-11/id/clips/test.csv \
  --checkpoint_dir stt-data/checkpoints \
  --export_dir stt-data/exported-model \
  --n_hidden 64 \
  --reduce_lr_on_plateau true \
  --plateau_epochs 8 \
  --plateau_reduction 0.08 \
  --early_stop true \
  --es_epochs 10 \
  --es_min_delta 0.06
```

### Dropout rate

In machine learning, one of the risks during training is that of [_overfitting_](https://en.wikipedia.org/wiki/Overfitting). _Overfitting_ is where training creates a model that does not _generalize_ well. That is, it _fits_ to only the set of data on which it is trained. During inference, new data is not recognised accurately.

_Dropout_ is a technical approach to reduce _overfitting_. In _dropout_, nodes are randomly removed from the neural network created during training. This simulates the effect of more diverse data, and is a computationally cheap way of reducing _overfitting_, and improving the _generalizability_ of the model.

_Dropout_ can be set for any layer of a neural network. The parameter that has the most effect for 🐸STT training is `--dropout_rate`, which controls  the feedforward layers of the neural network. To see the full set of _dropout parameters_, consult the 🐸STT documentation.

* The `-dropout_rate` parameter specifies how many nodes should be dropped from the neural network during training. The default value is `0.05`. However, if you are training on less than thousands of hours of voice data, you will find a value of `0.3` to `0.4` works better to prevent overfitting.

An example of training with this parameter would be:

```
python3 train.py \
  --train_files stt-data/cv-corpus-6.1-2020-12-11/id/clips/train.csv \
  --dev_files stt-data/cv-corpus-6.1-2020-12-11/id/clips/dev.csv \
  --test_files stt-data/cv-corpus-6.1-2020-12-11/id/clips/test.csv \
  --checkpoint_dir stt-data/checkpoints \
  --export_dir stt-data/exported-model \
  --n_hidden 64 \
  --reduce_lr_on_plateau true \
  --plateau_epochs 8 \
  --plateau_reduction 0.08 \
  --early_stop true \
  --es_epochs 10 \
  --es_min_delta 0.06 \
  --dropout_rate 0.3
```

## Steps and epochs

In training, a _step_ is one update of the [gradient](https://en.wikipedia.org/wiki/Gradient_descent); that is, one attempt to find the lowest, or minimal _loss_. The amount of processing done in one _step_ depends on the _batch size_. By default, `train.py` has a _batch size_ of `1`. That is, it processes one audio file in each _step_.

An _epoch_ is one full cycle through the training data. That is, if you have 1000 files listed in your `train.tsv` file, then you will expect to process 1000 _steps_ per epoch (assuming a _batch size_ of `1`).

To find out how many _steps_ to expect in each _epoch_, you can count the number of lines in your `train.tsv` file:

```
~/stt-data/cv-corpus-6.1-2020-12-11/id$ wc -l train.tsv
2131 train.tsv
```

In this case there would be `2131` _steps_ per _epoch_.

* `--epochs` specifies how many _epochs_ to train. It has a default of `75`, which would be appropriate for training tens to hundreds of hours of audio. If you have thousands of hours of audio, you may wish to increase the number of _epochs_ to around 150-300.

* `--train_batch_size`, `--dev_batch_size`, `--test_batch_size` all specify the _batch size_ per _step_. These all have a default value of `1`. Increasing the _batch size_ increases the amount of memory required to process the _step_; you need to be aware of this before increasing the _batch size_.

## Advanced training options

Advanced training options are available, such as _feature cache_ and _augmentation_. They are beyond the scope of this PlayBook, but you can [read more about them in the 🐸STT documentation](https://stt.readthedocs.io/en/latest/TRAINING.html#augmentation).

For a full list of parameters that can be passed to the `train.py` file, [please consult the 🐸STT documentation](https://stt.readthedocs.io/en/latest/Flags.html#training-flags).

## Monitoring GPU use with `nvtop`

In a separate terminal (ie not from the session where you have the Docker container open), run the command `nvtop`. You should see the `train.py` process consuming all available GPUs.

If you _do not_ see the GPU(s) being heavily utilised, you may be training only on your CPUs and you should double check your [environment](ENVIRONMENT.md).

## Possible errors

### `Failed to get convolution algorithm. This is probably because cuDNN failed to initialize, so try looking to see if a warning log message was printed above.` error when training

_You can safely skip this section if you have not encountered this error_

There have been several reports of an error similar to the below when training is initiated. Anecdotal evidence suggests that the error is more likely to be encountered if you are training using an RTX-model GPU.

The error will look like this:

```
Epoch 0 |   Training | Elapsed Time: 0:00:00 | Steps: 0 | Loss: 0.000000Traceback (most recent call last):
  File "/usr/local/lib/python3.6/dist-packages/tensorflow_core/python/client/session.py", line 1365, in _do_call
    return fn(*args)
  File "/usr/local/lib/python3.6/dist-packages/tensorflow_core/python/client/session.py", line 1350, in _run_fn
    target_list, run_metadata)
  File "/usr/local/lib/python3.6/dist-packages/tensorflow_core/python/client/session.py", line 1443, in _call_tf_sessionrun
    run_metadata)
tensorflow.python.framework.errors_impl.UnknownError: 2 root error(s) found.
  (0) Unknown: Failed to get convolution algorithm. This is probably because cuDNN failed to initialize, so try looking to see if a warning log message was printed above.
	 [[{{node tower_0/conv1d}}]]
	 [[concat/concat/_99]]
  (1) Unknown: Failed to get convolution algorithm. This is probably because cuDNN failed to initialize, so try looking to see if a warning log message was printed above.
	 [[{{node tower_0/conv1d}}]]
0 successful operations.
0 derived errors ignored.
```

To work around this error, you will need to set the `TF_FORCE_GPU_ALLOW_GROWTH` flag to `True`.

This is done in the file

`STT/training/coqui_stt_training/util/config.py`

and you should edit it as below:

```
root@687a2e3516d7:/STT/training/coqui_stt_training/util# nano config.py

...

    # Standard session configuration that'll be used for all new sessions.
    c.session_config = tfv1.ConfigProto(allow_soft_placement=True, log_device$
                                        inter_op_parallelism_threads=FLAGS.in$
                                        intra_op_parallelism_threads=FLAGS.in$

                                        gpu_options=tfv1.GPUOptions(allow_gro$

    # Set TF_FORCE_GPU_ALLOW_GROWTH to work around cuDNN error on RTX GPUs
    c.session_config.gpu_options.allow_growth=True
```

---

[Home](README.md) | [Previous - Setting up your Coqui STT training environment](ENVIRONMENT.md) | [Next - Testing and evaluating your trained model](TESTING.md)
