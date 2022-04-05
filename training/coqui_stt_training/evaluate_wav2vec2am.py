#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import csv
import io
import json
import os
import sys
from functools import partial
from multiprocessing import JoinableQueue, Manager, Process, cpu_count
from pathlib import Path

import numpy as np
import onnxruntime
import soundfile as sf
from clearml import Task
from coqui_stt_training.util.evaluate_tools import calculate_and_print_report
from coqui_stt_training.util.multiprocessing import PoolBase
from coqui_stt_ctcdecoder import (
    Alphabet,
    Scorer,
    ctc_beam_search_decoder_for_wav2vec2am,
)
from tqdm import tqdm


class CollectEmissionsPool(PoolBase):
    def init(self, model_file):
        sess_options = onnxruntime.SessionOptions()
        sess_options.graph_optimization_level = (
            onnxruntime.GraphOptimizationLevel.ORT_ENABLE_ALL
        )
        self.session = onnxruntime.InferenceSession(model_file, sess_options)

        parent_dir = Path(model_file).parent
        with open(parent_dir / "config.json") as fin:
            config = json.load(fin)

        self.am_alphabet = Alphabet()
        self.am_alphabet.InitFromLabels(config["alphabet_labels"])

    def run(self, wav_filename):
        speech_array, sr = sf.read(wav_filename)
        max_length = 250000
        speech_array = speech_array.astype(np.float32)
        features = speech_array[:max_length]

        def norm(wav, db_level=-27):
            r = 10 ** (db_level / 20)
            a = np.sqrt((len(wav) * (r**2)) / np.sum(wav**2))
            return wav * a

        features = norm(features)

        onnx_outputs = self.session.run(
            None, {self.session.get_inputs()[0].name: [features]}
        )[0].squeeze()

        return onnx_outputs


class EvaluationPool(PoolBase):
    def init(self, model_file, scorer_path, scorer_alphabet_path):
        parent_dir = Path(model_file).parent
        with open(parent_dir / "config.json") as fin:
            config = json.load(fin)

        self.am_alphabet = Alphabet()
        self.am_alphabet.InitFromLabels(config["alphabet_labels"])

        self.scorer = None
        if scorer_path:
            self.scorer_alphabet = Alphabet(scorer_alphabet_path)

            self.scorer = Scorer()
            self.scorer.init_from_filepath(
                scorer_path.encode("utf-8"),
                self.scorer_alphabet,
            )

        self.blank_id = config.get("blank_id", 0)
        self.raw_vocab = config["raw_vocab"]
        self.ignored_symbols = set(config["ignored_symbols"])

        if scorer_path:
            scorer_alphabet_labels = [
                s.decode("utf-8") for s in self.scorer_alphabet.GetLabels()
            ]

            for idx, label in enumerate(config["alphabet_labels"]):
                if label not in scorer_alphabet_labels:
                    self.ignored_symbols |= frozenset([idx])

    def run(self, job):
        wav_filename, emission, ground_truth, beam_width, lm_alpha, lm_beta = job
        prediction = self.transcribe_file(emission, beam_width, lm_alpha, lm_beta)
        return wav_filename, ground_truth, prediction

    def transcribe_file(self, emission, beam_width, lm_alpha, lm_beta):
        if lm_alpha is not None and lm_beta is not None:
            self.scorer.reset_params(lm_alpha, lm_beta)

        decoded = ctc_beam_search_decoder_for_wav2vec2am(
            emission,
            self.am_alphabet,
            beam_size=beam_width,
            scorer=self.scorer,
            blank_id=self.blank_id,
            ignored_symbols=list(self.ignored_symbols),
        )[0].transcript.strip()

        return decoded


def compute_emissions(model_file, csv_file, num_processes):
    jobs = []
    with open(csv_file, "r") as csvfile:
        csvreader = csv.DictReader(csvfile)
        for row in csvreader:
            # Relative paths are relative to the folder the CSV file is in
            if not os.path.isabs(row["wav_filename"]):
                row["wav_filename"] = os.path.join(
                    os.path.dirname(csv_file), row["wav_filename"]
                )
            jobs.append(row["wav_filename"])

    with CollectEmissionsPool.create(
        processes=num_processes, initargs=(model_file,)
    ) as pool:
        process_iterable = tqdm(
            pool.imap(jobs),
            desc="Collecting acoustic model emissions",
            total=len(jobs),
        )

        emissions = []
        for emission in process_iterable:
            emissions.append(emission)

    return emissions


def evaluate_from_emissions(
    model_file,
    csv_file,
    emissions,
    scorer,
    scorer_alphabet_path,
    num_processes,
    dump_to_file,
    beam_width,
    lm_alpha=None,
    lm_beta=None,
):
    jobs = []
    with open(csv_file, "r") as csvfile:
        csvreader = csv.DictReader(csvfile)
        for emission, row in zip(emissions, csvreader):
            # Relative paths are relative to the folder the CSV file is in
            if not os.path.isabs(row["wav_filename"]):
                row["wav_filename"] = os.path.join(
                    os.path.dirname(csv_file), row["wav_filename"]
                )
            jobs.append(
                (
                    row["wav_filename"],
                    emission,
                    row["transcript"],
                    beam_width,
                    lm_alpha,
                    lm_beta,
                )
            )

    with EvaluationPool.create(
        processes=num_processes, initargs=(model_file, scorer, scorer_alphabet_path)
    ) as pool:
        process_iterable = tqdm(
            pool.imap_unordered(jobs),
            desc="Transcribing files",
            total=len(jobs),
        )

        wav_filenames = []
        ground_truths = []
        predictions = []
        losses = []

        for wav_filename, ground_truth, prediction in process_iterable:
            wav_filenames.append(wav_filename)
            ground_truths.append(ground_truth)
            predictions.append(prediction)
            losses.append(0.0)

    # Print test summary
    samples = calculate_and_print_report(
        wav_filenames, ground_truths, predictions, losses, csv_file
    )

    if dump_to_file:
        with open(dump_to_file + ".txt", "w") as ftxt, open(
            dump_to_file + ".out", "w"
        ) as fout:
            for wav, txt, out in zip(wav_filenames, ground_truths, predictions):
                ftxt.write("%s %s\n" % (wav, txt))
                fout.write("%s %s\n" % (wav, out))
            print("Reference texts dumped to %s.txt" % dump_to_file)
            print("Transcription   dumped to %s.out" % dump_to_file)

    return samples


def evaluate_wav2vec2am(
    model_file,
    csv_file,
    scorer,
    scorer_alphabet_path,
    num_processes,
    dump_to_file,
    beam_width,
    lm_alpha=None,
    lm_beta=None,
    existing_pool=None,
):
    emissions = compute_emissions(model_file, csv_file, num_processes)
    return evaluate_from_emissions(
        model_file,
        csv_file,
        emissions,
        scorer,
        scorer_alphabet_path,
        num_processes,
        dump_to_file,
        beam_width,
        lm_alpha,
        lm_beta,
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description="Evaluation report using Wav2vec2 ONNX AM"
    )
    parser.add_argument(
        "--model", required=True, help="Path to the model (ONNX export)"
    )
    parser.add_argument("--csv", required=True, help="Path to the CSV source file")
    parser.add_argument(
        "--scorer",
        required=False,
        default=None,
        help="Path to the external scorer file",
    )
    parser.add_argument(
        "--scorer_alphabet",
        type=str,
        required=False,
        default="",
        help="Path of alphabet file used for Scorer construction. Required if --scorer is specified",
    )
    parser.add_argument(
        "--lm_alpha",
        required=False,
        default=None,
        help="LM weight",
    )
    parser.add_argument(
        "--lm_beta",
        required=False,
        default=None,
        help="Word insertion bonus",
    )
    parser.add_argument(
        "--proc",
        required=False,
        default=cpu_count(),
        type=int,
        help="Number of processes to spawn, defaulting to number of CPUs",
    )
    parser.add_argument(
        "--dump",
        required=False,
        help='Path to dump the results as text file, with one line for each wav: "wav transcription".',
    )
    parser.add_argument(
        "--beam_width",
        required=False,
        default=8,
        type=int,
        help="Beam width to use when decoding.",
    )
    parser.add_argument(
        "--clearml_project",
        required=False,
        default="STT/wav2vec2 decoding",
    )
    parser.add_argument(
        "--clearml_task",
        required=False,
        default="evaluation report",
    )
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    task = Task.init(project_name=args.clearml_project, task_name=args.clearml_task)
    if args.lm_alpha is not None:
        args.lm_alpha = float(args.lm_alpha)
    if args.lm_beta is not None:
        args.lm_beta = float(args.lm_beta)
    evaluate_wav2vec2am(
        args.model,
        args.csv,
        args.scorer,
        args.scorer_alphabet,
        args.proc,
        args.dump,
        args.beam_width,
        args.lm_alpha,
        args.lm_beta,
    )


if __name__ == "__main__":
    main()
