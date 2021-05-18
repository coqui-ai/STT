.. _checkpointing:

Checkpointing
=============

Checkpoints are representations of the parameters of a neural network. During training, model parameters are continually updated, and checkpoints allow graceful interruption of a training run without data loss. If you interrupt a training run for any reason, you can pick up where you left off by using the checkpoints as a starting place. This is the exact same logic behind :ref:`model fine-tuning <transfer-learning>`.

Checkpointing occurs at a configurable time interval. Resuming from checkpoints happens automatically by re-starting training with the same ``--checkpoint_dir`` of the former run. Alternatively, you can specify more fine grained options with ``--load_checkpoint_dir`` and ``--save_checkpoint_dir``, which specify separate locations to use for loading and saving checkpoints respectively.

Be aware that checkpoints are only valid for the same model geometry from which they were generated. If you experience error messages that certain ``Tensors`` have incompatible dimensions, you might be trying to use checkpoints with an incompatible architecture.
