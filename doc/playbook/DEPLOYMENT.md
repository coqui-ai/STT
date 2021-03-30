[Home](README.md) | [Previous - Testing and evaluating your trained model](TESTING.md) | [Next - Real life examples of using Coqui STT](EXAMPLES.md)

# Deployment

## Contents

- [Deployment](#deployment)
  * [Contents](#contents)
  * [Protocol buffer and memory mappable file formats](#protocol-buffer-and-memory-mappable-file-formats)
  * [Exporting a memory mappable protocol buffer file with `graphdef`](#exporting-a-memory-mappable-protocol-buffer-file-with--graphdef-)
  * [Exporting a tflite model](#exporting-a-tflite-model)

Now that you have [trained](TRAINING.md) and [evaluated](TESTING.md) your model, you are ready to use it for _inference_ - where spoken phrases - _utterances_ - are assessed by your trained model and a text _transcription_ provided.

There are some things to be aware of during this stage of the process.

## Protocol buffer and memory mappable file formats

By default, 🐸STT will export the trained model as a `.pb` file, such as:

```
$ sudo ls -las volumes/stt-data/_data/exported-model

     4 drwxr-xr-x 2 root root      4096 Feb  1 22:13 .
     4 drwxr-xr-x 6 root root      4096 Feb  1 22:23 ..
     4 -rwxr-xr-x 1 root root      1586 Feb  1 22:13 author_model_0.0.1.md
184488 -rwxr-xr-x 1 root root 188915369 Feb  1 22:13 output_graph.pb
```

A `.pb` file is a [protocol buffer](https://en.wikipedia.org/wiki/Protocol_Buffers) file. Protocol buffer is a widely used file format for trained models, but it has a significant downsides. It is not _memory mappable_. [Memory mappable](https://en.wikipedia.org/wiki/Memory-mapped_file) files can be referenced by the operating system using a _file descriptor_, and they consume far less memory than non-memory-mappable files. Protocol buffer files also tend to be much larger than memory-mappable files.

Most inference libraries, such as TensorFlow, require a memory-mappable format.

There are two formats in particular that you should be familiar with.

## Exporting a memory mappable protocol buffer file with `graphdef`

Using the `graphdef` tool which is built in to TensorFlow (but deprecated in TensorFlow 2.3), you can export a memory-mappable protocol buffer file using the following commands:

```
convert_graphdef_memmapped_format --in_graph=output_graph.pb --out_graph=output_graph.pbmm
```

where `--in_graph` is a path to your `.pb` file and `--out_graph` is a path to the exported memory-mappable protocol buffer file.

```
root@12a4ee8ce1ed:/STT# ./convert_graphdef_memmapped_format \
  --in_graph="persistent-data/exported-model/output_graph.pb" \
  --out_graph="persistent-data/exported-model/output_graph.pbmm"
2021-02-03 21:13:09.516709: W tensorflow/core/framework/cpu_allocator_impl.cc:81] Allocation of 134217728 exceeds 10% of system memory.
2021-02-03 21:13:09.647395: I tensorflow/contrib/util/convert_graphdef_memmapped_format_lib.cc:171] Converted 7 nodes
```

For [more information on creating a memory-mappable protocol buffer file, consult the documentation](https://stt.readthedocs.io/en/latest/TRAINING.html#exporting-a-model-for-inference).

***Be aware that this file format is likely to be deprecated in the future. We strongly recommend the use of `tflite`.***

## Exporting a tflite model

The `tflite` engine ([more information on tflite](https://www.tensorflow.org/lite/)) is designed to allow inference on mobile, IoT and embedded devices. If you have _not_ yet trained a model, and you want to export a model compatible with `tflite`, you will need to use the `--export_tflite` flags with the `train.py` script. For example:

```
python3 train.py \
  --train_files stt-data/cv-corpus-6.1-2020-12-11/id/clips/train.csv \
  --dev_files stt-data/cv-corpus-6.1-2020-12-11/id/clips/dev.csv \
  --test_files stt-data/cv-corpus-6.1-2020-12-11/id/clips/test.csv \
  --checkpoint_dir stt-data/checkpoints \
  --export_dir stt-data/exported-model \
  --export_tflite
```

If you have _already_ trained a model, and wish to export to `tflite` format, you can re-export it by specifying the same `checkpoint_dir` that you used for training, and by passing the `--export_tflite` parameter.

Here is an example:

```

python3 train.py \
   --checkpoint_dir persistent-data/checkpoints \
   --export_dir persistent-data/exported-model \
   --export_tflite

   I Loading best validating checkpoint from persistent-data/checkpoints-1feb2021-id/best_dev-34064
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
   I Models exported at persistent-data/exported-model
   I Model metadata file saved to persistent-data/exported-model/author_model_0.0.1.md. Before submitting the exported model for publishing make sure all information in the metadata file is correct, and complete the URL fields.

root@0913858a2868:/STT/persistent-data/exported-model# ls -las
total 415220
     4 drwxr-xr-x 2 root root      4096 Feb  3 22:42 .
     4 drwxr-xr-x 7 root root      4096 Feb  3 21:54 ..
     4 -rwxr-xr-x 1 root root      1582 Feb  3 22:42 author_model_0.0.1.md
184488 -rwxr-xr-x 1 root root 188915369 Feb  1 11:13 output_graph.pb
184496 -rw-r--r-- 1 root root 188916323 Feb  3 21:13 output_graph.pbmm
 46224 -rw-r--r-- 1 root root  47332112 Feb  3 22:42 output_graph.tflite

```

For more information on exporting a `tflite` model, [please consult the documentation](https://stt.readthedocs.io/en/latest/TRAINING.html#exporting-a-model-for-inference).

---

[Home](README.md) | [Previous - Testing and evaluating your trained model](TESTING.md) | [Next - Real life examples of using Coqui STT](EXAMPLES.md)
