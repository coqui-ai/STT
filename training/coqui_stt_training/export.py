#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys

LOG_LEVEL_INDEX = sys.argv.index("--log_level") + 1 if "--log_level" in sys.argv else 0
DESIRED_LOG_LEVEL = (
    sys.argv[LOG_LEVEL_INDEX] if 0 < LOG_LEVEL_INDEX < len(sys.argv) else "3"
)
os.environ["TF_CPP_MIN_LOG_LEVEL"] = DESIRED_LOG_LEVEL

import numpy as np
import tensorflow as tf
import tensorflow.compat.v1 as tfv1
import shutil

from .deepspeech_model import create_inference_graph, create_model, reset_default_graph
from .util.checkpoints import load_graph_for_evaluation
from .util.config import Config, initialize_globals_from_cli, log_error, log_info
from .util.feeding import wavfile_bytes_to_features
from .util.io import (
    open_remote,
    rmtree_remote,
    listdir_remote,
    is_remote_path,
    isdir_remote,
)


def file_relative_read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


def export():
    r"""
    Restores the trained variables into a simpler graph that will be exported for serving.
    """
    log_info("Exporting the model...")

    if Config.export_savedmodel:
        return export_savedmodel()

    reset_default_graph()

    inputs, outputs, _ = create_inference_graph(
        batch_size=Config.export_batch_size,
        n_steps=Config.n_steps,
        tflite=Config.export_tflite,
    )

    graph_version = int(file_relative_read("GRAPH_VERSION").strip())
    assert graph_version > 0

    # native_client: these nodes's names and shapes are part of the API boundary
    #   with the native client, if you change them you should sync changes with
    #   the C++ code.
    outputs["metadata_version"] = tf.constant([graph_version], name="metadata_version")
    outputs["metadata_sample_rate"] = tf.constant(
        [Config.audio_sample_rate], name="metadata_sample_rate"
    )
    outputs["metadata_feature_win_len"] = tf.constant(
        [Config.feature_win_len], name="metadata_feature_win_len"
    )
    outputs["metadata_feature_win_step"] = tf.constant(
        [Config.feature_win_step], name="metadata_feature_win_step"
    )
    outputs["metadata_beam_width"] = tf.constant(
        [Config.export_beam_width], name="metadata_beam_width"
    )
    outputs["metadata_alphabet"] = tf.constant(
        [Config.alphabet.Serialize()], name="metadata_alphabet"
    )

    if Config.export_language:
        outputs["metadata_language"] = tf.constant(
            [Config.export_language.encode("utf-8")], name="metadata_language"
        )

    # Prevent further graph changes
    tfv1.get_default_graph().finalize()

    output_names_tensors = [
        tensor.op.name for tensor in outputs.values() if isinstance(tensor, tf.Tensor)
    ]
    output_names_ops = [
        op.name for op in outputs.values() if isinstance(op, tf.Operation)
    ]
    output_names = output_names_tensors + output_names_ops

    with tf.Session() as session:
        # Restore variables from checkpoint
        load_graph_for_evaluation(session)

        output_filename = Config.export_file_name + ".pb"
        if Config.remove_export:
            if isdir_remote(Config.export_dir):
                log_info("Removing old export")
                rmtree_remote(Config.export_dir)

        output_graph_path = os.path.join(Config.export_dir, output_filename)

        if not is_remote_path(Config.export_dir) and not os.path.isdir(
            Config.export_dir
        ):
            os.makedirs(Config.export_dir)

        frozen_graph = tfv1.graph_util.convert_variables_to_constants(
            sess=session,
            input_graph_def=tfv1.get_default_graph().as_graph_def(),
            output_node_names=output_names,
        )

        frozen_graph = tfv1.graph_util.extract_sub_graph(
            graph_def=frozen_graph, dest_nodes=output_names
        )

        if not Config.export_tflite:
            with open_remote(output_graph_path, "wb") as fout:
                fout.write(frozen_graph.SerializeToString())
        else:
            output_tflite_path = os.path.join(
                Config.export_dir, output_filename.replace(".pb", ".tflite")
            )

            try:
                converter = tf.lite.TFLiteConverter(
                    frozen_graph,
                    input_tensors=inputs.values(),
                    output_tensors=outputs.values(),
                )
            except AttributeError:
                log_error(
                    "Couldn't access TFLite API in TensorFlow package. "
                    "The NVIDIA TF1 docker image removes the TFLite API, so you'll need "
                    "to use the separate virtual environment to call the export module: \n"
                    "    /tflite-venv/bin/python -m coqui_stt_training.export --checkpoint_dir ... --export_dir ...\n"
                    "You can also save the checkpoint outside of Docker and then export it using "
                    "the training package directly: \n"
                    "    pip install coqui_stt_training\n"
                    "    python -m coqui_stt_training.export --checkpoint_dir ... --export_dir ...\n"
                    "This should work without needing any special CUDA setup, even for CUDA checkpoints."
                )
                sys.exit(1)

            if Config.export_quantize:
                converter.optimizations = [tf.lite.Optimize.DEFAULT]

            # AudioSpectrogram and Mfcc ops are custom but have built-in kernels in TFLite
            converter.allow_custom_ops = True
            tflite_model = converter.convert()

            with open_remote(output_tflite_path, "wb") as fout:
                fout.write(tflite_model)

        log_info("Models exported at %s" % (Config.export_dir))

    metadata_fname = os.path.join(
        Config.export_dir,
        "{}_{}_{}.md".format(
            Config.export_author_id,
            Config.export_model_name,
            Config.export_model_version,
        ),
    )

    model_runtime = "tflite" if Config.export_tflite else "tensorflow"
    with open_remote(metadata_fname, "w") as f:
        f.write("---\n")
        f.write("author: {}\n".format(Config.export_author_id))
        f.write("model_name: {}\n".format(Config.export_model_name))
        f.write("model_version: {}\n".format(Config.export_model_version))
        f.write("contact_info: {}\n".format(Config.export_contact_info))
        f.write("license: {}\n".format(Config.export_license))
        f.write("language: {}\n".format(Config.export_language))
        f.write("runtime: {}\n".format(model_runtime))
        f.write("min_stt_version: {}\n".format(Config.export_min_stt_version))
        f.write("max_stt_version: {}\n".format(Config.export_max_stt_version))
        f.write(
            "acoustic_model_url: <replace this with a publicly available URL of the acoustic model>\n"
        )
        f.write(
            "scorer_url: <replace this with a publicly available URL of the scorer, if present>\n"
        )
        f.write("---\n")
        f.write("{}\n".format(Config.export_description))

    log_info(
        "Model metadata file saved to {}. Before submitting the exported model for publishing make sure all information in the metadata file is correct, and complete the URL fields.".format(
            metadata_fname
        )
    )


def export_savedmodel():
    reset_default_graph()

    with tfv1.Session(config=Config.session_config) as session:
        input_wavfile_contents = tf.placeholder(
            tf.string, [], name="input_wavfile_contents"
        )
        features, features_len = wavfile_bytes_to_features(input_wavfile_contents)

        features_in = tf.placeholder(
            tf.float32, [None, None, Config.n_input], name="features_in"
        )
        feature_lens_in = tf.placeholder(tf.int32, [None], name="feature_lens_in")
        batch_size = tf.shape(features_in)[0]

        previous_state_c = tf.zeros([batch_size, Config.n_cell_dim], tf.float32)
        previous_state_h = tf.zeros([batch_size, Config.n_cell_dim], tf.float32)

        previous_state = tf.nn.rnn_cell.LSTMStateTuple(
            previous_state_c, previous_state_h
        )

        # One rate per layer
        no_dropout = [None] * 6

        logits, layers = create_model(
            batch_x=features_in,
            seq_length=feature_lens_in,
            dropout=no_dropout,
            previous_state=previous_state,
        )
        # Transpose to batch major and softmax for decoder
        probs = tf.nn.softmax(tf.transpose(logits, [1, 0, 2]))

        # Restore variables from training checkpoint
        load_graph_for_evaluation(session)

        builder = tfv1.saved_model.builder.SavedModelBuilder(Config.export_dir)

        input_file_tinfo = tfv1.saved_model.utils.build_tensor_info(
            input_wavfile_contents
        )
        input_feat_tinfo = tfv1.saved_model.utils.build_tensor_info(features_in)
        input_feat_lens_tinfo = tfv1.saved_model.utils.build_tensor_info(
            feature_lens_in
        )
        output_feats_tinfo = tfv1.saved_model.utils.build_tensor_info(features)
        output_feat_lens_tinfo = tfv1.saved_model.utils.build_tensor_info(features_len)
        output_probs_tinfo = tfv1.saved_model.utils.build_tensor_info(probs)

        compute_feats_sig = tfv1.saved_model.signature_def_utils.build_signature_def(
            inputs={
                "input_wavfile": input_file_tinfo,
            },
            outputs={
                "features": output_feats_tinfo,
                "features_len": output_feat_lens_tinfo,
            },
            method_name="compute_features",
        )

        from_feats_sig = tfv1.saved_model.signature_def_utils.build_signature_def(
            inputs={
                "features": input_feat_tinfo,
                "features_len": input_feat_lens_tinfo,
            },
            outputs={
                "probs": output_probs_tinfo,
            },
            method_name="forward_from_features",
        )

        builder.add_meta_graph_and_variables(
            session,
            [tfv1.saved_model.tag_constants.SERVING],
            signature_def_map={
                "compute_features": compute_feats_sig,
                "forward_from_features": from_feats_sig,
            },
        )

        builder.save()

        # Copy scorer and alphabet alongside SavedModel
        if Config.scorer_path:
            shutil.copy(
                Config.scorer_path, os.path.join(Config.export_dir, "exported.scorer")
            )
        shutil.copy(
            Config.effective_alphabet_path,
            os.path.join(Config.export_dir, "alphabet.txt"),
        )

        log_info(f"Exported SavedModel to {Config.export_dir}")


def package_zip():
    # --export_dir path/to/export/LANG_CODE/ => path/to/export/LANG_CODE.zip
    export_dir = os.path.join(
        os.path.abspath(Config.export_dir), ""
    )  # Force ending '/'
    if is_remote_path(export_dir):
        log_error(
            "Cannot package remote path zip %s. Please do this manually." % export_dir
        )
        return

    zip_filename = os.path.dirname(export_dir)

    shutil.copy(Config.scorer_path, export_dir)

    archive = shutil.make_archive(zip_filename, "zip", export_dir)
    log_info("Exported packaged model {}".format(archive))


def main():
    initialize_globals_from_cli()

    if not Config.export_dir:
        raise RuntimeError(
            "Calling export script directly but no --export_dir specified"
        )

    if not Config.export_zip:
        # Export to folder
        export()
    else:
        if listdir_remote(Config.export_dir):
            raise RuntimeError(
                "Directory {} is not empty, please fix this.".format(Config.export_dir)
            )

        export()
        package_zip()


if __name__ == "__main__":
    main()
