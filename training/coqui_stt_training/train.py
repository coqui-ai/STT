#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import os
import sys

LOG_LEVEL_INDEX = sys.argv.index("--log_level") + 1 if "--log_level" in sys.argv else 0
DESIRED_LOG_LEVEL = (
    sys.argv[LOG_LEVEL_INDEX] if 0 < LOG_LEVEL_INDEX < len(sys.argv) else "3"
)
os.environ["TF_CPP_MIN_LOG_LEVEL"] = DESIRED_LOG_LEVEL

import time
from datetime import datetime
from pathlib import Path

import numpy as np
import progressbar
import tensorflow.compat.v1 as tfv1
import tensorflow as tf
from coqui_stt_ctcdecoder import Scorer

tfv1.logging.set_verbosity(
    {
        "0": tfv1.logging.DEBUG,
        "1": tfv1.logging.INFO,
        "2": tfv1.logging.WARN,
        "3": tfv1.logging.ERROR,
    }.get(DESIRED_LOG_LEVEL)
)


from . import evaluate
from . import export
from . import training_graph_inference
from .deepspeech_model import (
    create_model,
    rnn_impl_lstmblockfusedcell,
    rnn_impl_cudnn_rnn,
    reset_default_graph,
)
from .util.augmentations import NormalizeSampleRate
from .util.checkpoints import (
    load_graph_for_evaluation,
    load_or_init_graph_for_training,
    reload_best_checkpoint,
)
from .util.config import (
    Config,
    create_progressbar,
    initialize_globals_from_cli,
    log_debug,
    log_error,
    log_info,
    log_progress,
    log_warn,
)
from .util.feeding import create_dataset
from .util.helpers import check_ctcdecoder_version
from .util.io import remove_remote


# Accuracy and Loss
# =================

# In accord with 'Deep Speech: Scaling up end-to-end speech recognition'
# (http://arxiv.org/abs/1412.5567),
# the loss function used by our network should be the CTC loss function
# (http://www.cs.toronto.edu/~graves/preprint.pdf).
# Conveniently, this loss function is implemented in TensorFlow.
# Thus, we can simply make use of this implementation to define our loss.


def calculate_mean_edit_distance_and_loss(iterator, dropout, reuse):
    r"""
    This routine beam search decodes a mini-batch and calculates the loss and mean edit distance.
    Next to total and average loss it returns the mean edit distance,
    the decoded result and the batch's original Y.
    """
    # Obtain the next batch of data
    batch_filenames, (batch_x, batch_seq_len), batch_y = iterator.get_next()

    if Config.train_cudnn:
        rnn_impl = rnn_impl_cudnn_rnn
    else:
        rnn_impl = rnn_impl_lstmblockfusedcell

    # Calculate the logits of the batch
    logits, _ = create_model(
        batch_x, batch_seq_len, dropout, reuse=reuse, rnn_impl=rnn_impl
    )

    # Compute the CTC loss using TensorFlow's `ctc_loss`
    total_loss = tfv1.nn.ctc_loss(
        labels=batch_y, inputs=logits, sequence_length=batch_seq_len
    )

    # Check if any files lead to non finite loss
    non_finite_files = tf.gather(
        batch_filenames, tfv1.where(~tf.math.is_finite(total_loss))
    )

    # Calculate the average loss across the batch
    avg_loss = tf.reduce_mean(input_tensor=total_loss)

    # Finally we return the average loss
    return avg_loss, non_finite_files


# Adam Optimization
# =================

# In contrast to 'Deep Speech: Scaling up end-to-end speech recognition'
# (http://arxiv.org/abs/1412.5567),
# in which 'Nesterov's Accelerated Gradient Descent'
# (www.cs.toronto.edu/~fritz/absps/momentum.pdf) was used,
# we will use the Adam method for optimization (http://arxiv.org/abs/1412.6980),
# because, generally, it requires less fine-tuning.
def create_optimizer(learning_rate_var):
    optimizer = tfv1.train.AdamOptimizer(
        learning_rate=learning_rate_var,
        beta1=Config.beta1,
        beta2=Config.beta2,
        epsilon=Config.epsilon,
    )
    return optimizer


# Towers
# ======

# In order to properly make use of multiple GPU's, one must introduce new abstractions,
# not present when using a single GPU, that facilitate the multi-GPU use case.
# In particular, one must introduce a means to isolate the inference and gradient
# calculations on the various GPU's.
# The abstraction we intoduce for this purpose is called a 'tower'.
# A tower is specified by two properties:
# * **Scope** - A scope, as provided by `tf.name_scope()`,
# is a means to isolate the operations within a tower.
# For example, all operations within 'tower 0' could have their name prefixed with `tower_0/`.
# * **Device** - A hardware device, as provided by `tf.device()`,
# on which all operations within the tower execute.
# For example, all operations of 'tower 0' could execute on the first GPU `tf.device('/gpu:0')`.


def get_tower_results(iterator, optimizer, dropout_rates):
    r"""
    With this preliminary step out of the way, we can for each GPU introduce a
    tower for which's batch we calculate and return the optimization gradients
    and the average loss across towers.
    """
    # To calculate the mean of the losses
    tower_avg_losses = []

    # Tower gradients to return
    tower_gradients = []

    # Aggregate any non finite files in the batches
    tower_non_finite_files = []

    with tfv1.variable_scope(tfv1.get_variable_scope()):
        # Loop over available_devices
        for i in range(len(Config.available_devices)):
            # Execute operations of tower i on device i
            device = Config.available_devices[i]
            with tf.device(device):
                # Create a scope for all operations of tower i
                with tf.name_scope("tower_%d" % i):
                    # Calculate the avg_loss and mean_edit_distance and retrieve the decoded
                    # batch along with the original batch's labels (Y) of this tower
                    avg_loss, non_finite_files = calculate_mean_edit_distance_and_loss(
                        iterator, dropout_rates, reuse=i > 0
                    )

                    # Allow for variables to be re-used by the next tower
                    tfv1.get_variable_scope().reuse_variables()

                    # Retain tower's avg losses
                    tower_avg_losses.append(avg_loss)

                    # Compute gradients for model parameters using tower's mini-batch
                    gradients = optimizer.compute_gradients(avg_loss)

                    # Retain tower's gradients
                    tower_gradients.append(gradients)

                    tower_non_finite_files.append(non_finite_files)

    avg_loss_across_towers = tf.reduce_mean(input_tensor=tower_avg_losses, axis=0)
    tfv1.summary.scalar(
        name="step_loss", tensor=avg_loss_across_towers, collections=["step_summaries"]
    )

    all_non_finite_files = tf.concat(tower_non_finite_files, axis=0)

    # Return gradients and the average loss
    return tower_gradients, avg_loss_across_towers, all_non_finite_files


def average_gradients(tower_gradients):
    r"""
    A routine for computing each variable's average of the gradients obtained from the GPUs.
    Note also that this code acts as a synchronization point as it requires all
    GPUs to be finished with their mini-batch before it can run to completion.
    """
    # List of average gradients to return to the caller
    average_grads = []

    # Run this on cpu_device to conserve GPU memory
    with tf.device(Config.cpu_device):
        # Loop over gradient/variable pairs from all towers
        for grad_and_vars in zip(*tower_gradients):
            # Introduce grads to store the gradients for the current variable
            grads = []

            # Loop over the gradients for the current variable
            for g, _ in grad_and_vars:
                # Add 0 dimension to the gradients to represent the tower.
                expanded_g = tf.expand_dims(g, 0)
                # Append on a 'tower' dimension which we will average over below.
                grads.append(expanded_g)

            # Average over the 'tower' dimension
            grad = tf.concat(grads, 0)
            grad = tf.reduce_mean(input_tensor=grad, axis=0)

            # Create a gradient/variable tuple for the current variable with its average gradient
            grad_and_var = (grad, grad_and_vars[0][1])

            # Add the current tuple to average_grads
            average_grads.append(grad_and_var)

    # Return result to caller
    return average_grads


def early_training_checks():
    check_ctcdecoder_version()

    # Check for proper scorer early
    if Config.scorer_path:
        scorer = Scorer(
            Config.lm_alpha, Config.lm_beta, Config.scorer_path, Config.alphabet
        )
        del scorer

    if (
        Config.train_files
        and Config.test_files
        and Config.load_checkpoint_dir != Config.save_checkpoint_dir
    ):
        log_warn(
            "WARNING: You specified different values for --load_checkpoint_dir "
            "and --save_checkpoint_dir, but you are running training and testing "
            "in a single invocation. The testing phase has been disable to prevent "
            "unexpected behavior of testing on the base checkpoint rather than the "
            "trained one. You should train and evaluate in two separate commands, "
            "specifying the correct --load_checkpoint_dir in both cases.\nFor training, "
            "use: python -m coqui_stt_training.train\n"
            "For evaluation, use python -m coqui_stt_training.evaluate"
        )
        Config.test_files = []


def create_training_datasets(
    epoch_ph: tf.Tensor = None,
    reverse: bool = False,
    limit: int = 0,
) -> (tf.data.Dataset, [tf.data.Dataset], [tf.data.Dataset],):
    """Creates training datasets from input flags.

    Returns a single training dataset and two lists of datasets for validation
    and metrics tracking.
    """
    # Create training and validation datasets
    train_set = create_dataset(
        Config.train_files,
        batch_size=Config.train_batch_size,
        epochs=Config.epochs,
        augmentations=Config.augmentations,
        cache_path=Config.feature_cache,
        train_phase=True,
        process_ahead=len(Config.available_devices) * Config.train_batch_size * 2,
        reverse=reverse,
        limit=limit,
        buffering=Config.read_buffer,
        epoch_ph=epoch_ph,
    )

    dev_sets = []
    if Config.dev_files:
        dev_sets = [
            create_dataset(
                [source],
                batch_size=Config.dev_batch_size,
                train_phase=False,
                augmentations=[NormalizeSampleRate(Config.audio_sample_rate)],
                process_ahead=len(Config.available_devices) * Config.dev_batch_size * 2,
                reverse=reverse,
                limit=limit,
                buffering=Config.read_buffer,
            )
            for source in Config.dev_files
        ]

    metrics_sets = []
    if Config.metrics_files:
        metrics_sets = [
            create_dataset(
                [source],
                batch_size=Config.dev_batch_size,
                train_phase=False,
                augmentations=[NormalizeSampleRate(Config.audio_sample_rate)],
                process_ahead=len(Config.available_devices) * Config.dev_batch_size * 2,
                reverse=reverse,
                limit=limit,
                buffering=Config.read_buffer,
            )
            for source in Config.metrics_files
        ]

    return train_set, dev_sets, metrics_sets


def train():
    if not Config.skip_batch_test:
        log_info("Performing dummy training to check for memory problems.")
        log_info(
            "If the following process crashes, you likely have batch sizes "
            "that are too big for your available system memory (or GPU memory)."
        )
        train_impl(
            epochs=1, reverse=True, limit=Config.train_batch_size * 3, write=False
        )

        log_info(
            "Dummy run finished without problems, now starting real training process."
        )
    train_impl(epochs=Config.epochs, silent_load=True)


def train_impl(epochs=0, reverse=False, limit=0, write=True, silent_load=False):
    early_training_checks()

    reset_default_graph()
    tfv1.set_random_seed(Config.random_seed)

    epoch_ph = tf.placeholder(tf.int64, name="epoch_ph")
    train_set, dev_sets, metrics_sets = create_training_datasets(
        epoch_ph, reverse=reverse, limit=limit
    )

    iterator = tfv1.data.Iterator.from_structure(
        tfv1.data.get_output_types(train_set),
        tfv1.data.get_output_shapes(train_set),
        output_classes=tfv1.data.get_output_classes(train_set),
    )

    # Make initialization ops for switching between the two sets
    train_init_op = iterator.make_initializer(train_set)
    dev_init_ops = [iterator.make_initializer(dev_set) for dev_set in dev_sets]
    metrics_init_ops = [
        iterator.make_initializer(metrics_set) for metrics_set in metrics_sets
    ]

    # Dropout
    dropout_rates = [
        tfv1.placeholder(tf.float32, name="dropout_{}".format(i)) for i in range(6)
    ]
    dropout_feed_dict = {
        dropout_rates[0]: Config.dropout_rate,
        dropout_rates[1]: Config.dropout_rate2,
        dropout_rates[2]: Config.dropout_rate3,
        dropout_rates[3]: Config.dropout_rate4,
        dropout_rates[4]: Config.dropout_rate5,
        dropout_rates[5]: Config.dropout_rate6,
    }
    no_dropout_feed_dict = {rate: 0.0 for rate in dropout_rates}

    # Building the graph
    learning_rate_var = tfv1.get_variable(
        "learning_rate", initializer=Config.learning_rate, trainable=False
    )
    reduce_learning_rate_op = learning_rate_var.assign(
        tf.multiply(learning_rate_var, Config.plateau_reduction)
    )
    optimizer = create_optimizer(learning_rate_var)

    # Enable mixed precision training
    if Config.automatic_mixed_precision:
        log_info("Enabling automatic mixed precision training.")
        optimizer = tfv1.train.experimental.enable_mixed_precision_graph_rewrite(
            optimizer
        )

    gradients, loss, non_finite_files = get_tower_results(
        iterator, optimizer, dropout_rates
    )

    # Average tower gradients across GPUs
    avg_tower_gradients = average_gradients(gradients)

    # global_step is automagically incremented by the optimizer
    global_step = tfv1.train.get_or_create_global_step()
    apply_gradient_op = optimizer.apply_gradients(
        avg_tower_gradients, global_step=global_step
    )

    # Summaries
    step_summaries_op = (
        tfv1.summary.merge_all("step_summaries") if write else tf.no_op()
    )
    step_summary_writers = (
        {
            "train": tfv1.summary.FileWriter(
                os.path.join(Config.summary_dir, "train"), max_queue=120
            ),
            "dev": tfv1.summary.FileWriter(
                os.path.join(Config.summary_dir, "dev"), max_queue=120
            ),
            "metrics": tfv1.summary.FileWriter(
                os.path.join(Config.summary_dir, "metrics"), max_queue=120
            ),
        }
        if write
        else None
    )

    human_readable_set_names = {
        "train": "Training",
        "dev": "Validation",
        "metrics": "Metrics",
    }

    # Checkpointing
    checkpoint_saver = (
        tfv1.train.Saver(max_to_keep=Config.max_to_keep) if write else None
    )
    checkpoint_path = os.path.join(Config.save_checkpoint_dir, "train")

    best_dev_saver = tfv1.train.Saver(max_to_keep=1) if write else None
    best_dev_path = os.path.join(Config.save_checkpoint_dir, "best_dev")

    with tfv1.Session(config=Config.session_config) as session:
        log_debug("Session opened.")

        # Prevent further graph changes
        tfv1.get_default_graph().finalize()

        # Load checkpoint or initialize variables
        load_or_init_graph_for_training(session, silent=silent_load)

        def run_set(set_name, epoch, init_op, dataset=None):
            is_train = set_name == "train"
            train_op = apply_gradient_op if is_train else []
            feed_dict = dropout_feed_dict if is_train else no_dropout_feed_dict

            total_loss = 0.0
            step_count = 0

            checkpoint_time = time.time()

            if (
                write
                and is_train
                and Config.cache_for_epochs > 0
                and Config.feature_cache
            ):
                feature_cache_index = Config.feature_cache + ".index"
                if epoch % Config.cache_for_epochs == 0 and os.path.isfile(
                    feature_cache_index
                ):
                    log_info("Invalidating feature cache")
                    remove_remote(
                        feature_cache_index
                    )  # this will let TF also overwrite the related cache data files

            # Setup progress bar
            class LossWidget(progressbar.widgets.FormatLabel):
                def __init__(self):
                    progressbar.widgets.FormatLabel.__init__(
                        self, format="Loss: %(mean_loss)f"
                    )

                def __call__(self, progress, data, **kwargs):
                    data["mean_loss"] = total_loss / step_count if step_count else 0.0
                    return progressbar.widgets.FormatLabel.__call__(
                        self, progress, data, **kwargs
                    )

            prefix = "Epoch {} | {:>10}".format(
                epoch, human_readable_set_names[set_name]
            )
            widgets = [
                " | ",
                progressbar.widgets.Timer(),
                " | Steps: ",
                progressbar.widgets.Counter(),
                " | ",
                LossWidget(),
            ]
            suffix = " | Dataset: {}".format(dataset) if dataset else None
            pbar = create_progressbar(
                prefix=prefix, widgets=widgets, suffix=suffix
            ).start()

            # Initialize iterator to the appropriate dataset
            session.run(init_op, {epoch_ph: epoch})

            # Batch loop
            while True:
                try:
                    (
                        _,
                        current_step,
                        batch_loss,
                        problem_files,
                        step_summary,
                    ) = session.run(
                        [
                            train_op,
                            global_step,
                            loss,
                            non_finite_files,
                            step_summaries_op,
                        ],
                        feed_dict={**feed_dict, **{epoch_ph: epoch}},
                    )
                except tf.errors.OutOfRangeError:
                    break

                if problem_files.size > 0:
                    problem_files = [f.decode("utf8") for f in problem_files[..., 0]]
                    log_error(
                        "The following files caused an infinite (or NaN) "
                        "loss: {}".format(",".join(problem_files))
                    )

                total_loss += batch_loss
                step_count += 1

                pbar.update(step_count)

                if write:
                    step_summary_writers.get(set_name).add_summary(
                        step_summary, current_step
                    )

                if (
                    write
                    and is_train
                    and Config.checkpoint_secs > 0
                    and time.time() - checkpoint_time > Config.checkpoint_secs
                ):
                    checkpoint_saver.save(
                        session, checkpoint_path, global_step=current_step
                    )
                    checkpoint_time = time.time()

            pbar.finish()
            mean_loss = total_loss / step_count if step_count > 0 else 0.0
            return mean_loss, step_count

        log_info("STARTING Optimization")
        train_start_time = datetime.utcnow()
        best_dev_loss = float("inf")
        dev_losses = []
        epochs_without_improvement = 0
        try:
            for epoch in range(epochs):
                # Training
                log_progress("Training epoch %d..." % epoch)
                train_loss, _ = run_set("train", epoch, train_init_op)
                log_progress(
                    "Finished training epoch %d - loss: %f" % (epoch, train_loss)
                )
                if write:
                    checkpoint_saver.save(
                        session, checkpoint_path, global_step=global_step
                    )

                if Config.dev_files:
                    # Validation
                    dev_loss = 0.0
                    total_steps = 0
                    for source, init_op in zip(Config.dev_files, dev_init_ops):
                        log_progress("Validating epoch %d on %s..." % (epoch, source))
                        set_loss, steps = run_set("dev", epoch, init_op, dataset=source)
                        dev_loss += set_loss * steps
                        total_steps += steps
                        log_progress(
                            "Finished validating epoch %d on %s - loss: %f"
                            % (epoch, source, set_loss)
                        )

                    dev_loss = dev_loss / total_steps
                    dev_losses.append(dev_loss)

                    # Count epochs without an improvement for early stopping and reduction of learning rate on a plateau
                    # the improvement has to be greater than Config.es_min_delta
                    if dev_loss > best_dev_loss - Config.es_min_delta:
                        epochs_without_improvement += 1
                    else:
                        epochs_without_improvement = 0

                    # Save new best model
                    if write and dev_loss < best_dev_loss:
                        best_dev_loss = dev_loss
                        save_path = best_dev_saver.save(
                            session,
                            best_dev_path,
                            global_step=global_step,
                            latest_filename="best_dev_checkpoint",
                        )
                        log_info(
                            "Saved new best validating model with loss %f to: %s"
                            % (best_dev_loss, save_path)
                        )

                    # Early stopping
                    if (
                        Config.early_stop
                        and epochs_without_improvement == Config.es_epochs
                    ):
                        log_info(
                            "Early stop triggered as the loss did not improve the last {} epochs".format(
                                epochs_without_improvement
                            )
                        )
                        break

                    # Reduce learning rate on plateau
                    # If the learning rate was reduced and there is still no improvement
                    # wait Config.plateau_epochs before the learning rate is reduced again
                    if (
                        Config.reduce_lr_on_plateau
                        and epochs_without_improvement > 0
                        and epochs_without_improvement % Config.plateau_epochs == 0
                    ):
                        # Reload checkpoint that we use the best_dev weights again
                        reload_best_checkpoint(session)

                        # Reduce learning rate
                        session.run(reduce_learning_rate_op)
                        current_learning_rate = learning_rate_var.eval()
                        log_info(
                            "Encountered a plateau, reducing learning rate to {}".format(
                                current_learning_rate
                            )
                        )

                        # Overwrite best checkpoint with new learning rate value
                        if write:
                            save_path = best_dev_saver.save(
                                session,
                                best_dev_path,
                                global_step=global_step,
                                latest_filename="best_dev_checkpoint",
                            )
                            log_info(
                                "Saved best validating model with reduced learning rate to: %s"
                                % (save_path)
                            )

                if Config.metrics_files:
                    # Read only metrics, not affecting best validation loss tracking
                    for source, init_op in zip(Config.metrics_files, metrics_init_ops):
                        log_progress("Metrics for epoch %d on %s..." % (epoch, source))
                        set_loss, _ = run_set("metrics", epoch, init_op, dataset=source)
                        log_progress(
                            "Metrics for epoch %d on %s - loss: %f"
                            % (epoch, source, set_loss)
                        )

                print("-" * 80)

        except KeyboardInterrupt:
            pass
        log_info(
            "FINISHED optimization in {}".format(datetime.utcnow() - train_start_time)
        )
    log_debug("Session closed.")


def main():
    initialize_globals_from_cli()

    def deprecated_msg(prefix):
        return (
            f"{prefix} Using the training module as a generic driver for all training "
            "related functionality is deprecated and will be removed soon. Use "
            "the specific modules: \n"
            "    python -m coqui_stt_training.train\n"
            "    python -m coqui_stt_training.evaluate\n"
            "    python -m coqui_stt_training.export\n"
            "    python -m coqui_stt_training.training_graph_inference"
        )

    if Config.train_files:
        train()
    else:
        log_warn(deprecated_msg("Calling training module without --train_files."))

    if Config.test_files:
        log_warn(
            deprecated_msg(
                "Specifying --test_files when calling train module. Use python -m coqui_stt_training.evaluate"
            )
        )
        evaluate.test()

    if Config.export_dir:
        log_warn(
            deprecated_msg(
                "Specifying --export_dir when calling train module. Use python -m coqui_stt_training.export"
            )
        )
        export.export()

    if Config.one_shot_infer:
        log_warn(
            deprecated_msg(
                "Specifying --one_shot_infer when calling train module. Use python -m coqui_stt_training.training_graph_inference"
            )
        )
        traning_graph_inference.do_single_file_inference(Config.one_shot_infer)


if __name__ == "__main__":
    main()
