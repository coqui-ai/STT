.. _horovod-parallel-training:

Distributed training using Horovod
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you have a capable compute architecture, it is possible to distribute the training using `Horovod <https://github.com/horovod/horovod>`_. A fast network is recommended.
Horovod is capable of using MPI and NVIDIA's NCCL for highly optimized inter-process communication.
It also offers `Gloo <https://github.com/facebookincubator/gloo>`_ as an easy-to-setup communication backend.

For more information about setup or tuning of Horovod please visit `Horovod's documentation <https://horovod.readthedocs.io/en/stable/summary_include.html>`_.

Horovod is expected to run on heterogeneous systems (e.g. different number and model type of GPUs per machine).
However, this can cause unpredictable problems and user interaction in training code is needed.
Therefore, we do only support homogenous systems, which means same hardware and also same software configuration (OS, drivers, MPI, NCCL, TensorFlow, ...) on each machine.
The only exception is different number of GPUs per machine, since this can be controlled by ``horovodrun -H``.

Detailed documentation how to run Horovod is provided `here <https://horovod.readthedocs.io/en/stable/running.html>`_.
The short command to train on 4 machines using 4 GPUs each:

.. code-block:: bash

    horovodrun -np 16 -H server1:4,server2:4,server3:4,server4:4 python3 DeepSpeech.py --train_files [...] --horovod