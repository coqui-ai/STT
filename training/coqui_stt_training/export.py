#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys

LOG_LEVEL_INDEX = sys.argv.index("--log_level") + 1 if "--log_level" in sys.argv else 0
DESIRED_LOG_LEVEL = (
    sys.argv[LOG_LEVEL_INDEX] if 0 < LOG_LEVEL_INDEX < len(sys.argv) else "3"
)
os.environ["TF_CPP_MIN_LOG_LEVEL"] = DESIRED_LOG_LEVEL

import tensorflow as tf
import tensorflow.compat.v1 as tfv1
import shutil

from .deepspeech_model import create_inference_graph
from .util.checkpoints import load_graph_for_evaluation
from .util.config import Config, initialize_globals_from_cli, log_error, log_info
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

    tfv1.reset_default_graph()

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

            converter = tf.lite.TFLiteConverter(
                frozen_graph,
                input_tensors=inputs.values(),
                output_tensors=outputs.values(),
            )

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
