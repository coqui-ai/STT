#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import csv
import os
import sys
import io
from functools import partial
from multiprocessing import JoinableQueue, Manager, Process, cpu_count

import numpy as np
import onnxruntime
import soundfile as sf
from clearml import Task
from coqui_stt_training.util.evaluate_tools import calculate_and_print_report
from coqui_stt_ctcdecoder import (
    Alphabet,
    Scorer,
    ctc_beam_search_decoder_for_wav2vec2am,
)


def evaluation_worker(model, scorer_path, queue_in, queue_out, beam_width):
    sess_options = onnxruntime.SessionOptions()
    sess_options.graph_optimization_level = (
        onnxruntime.GraphOptimizationLevel.ORT_ENABLE_ALL
    )
    session = onnxruntime.InferenceSession(model, sess_options)

    am_alphabet = Alphabet()
    am_alphabet.InitFromLabels("ABCD etaonihsrdlumwcfgypbvk'xjqz")

    scorer = None
    if scorer_path:
        scorer_alphabet = Alphabet()
        scorer_alphabet.InitFromLabels(" abcdefghijklmnopqrstuvwxyz'")

        scorer = Scorer()
        scorer.init_from_filepath(scorer_path.encode("utf-8"), scorer_alphabet)

    while True:
        try:
            msg = queue_in.get()
            filename = msg["filename"]

            speech_array, sr = sf.read(filename)
            max_length = 250000
            speech_array = speech_array.astype(np.float32)
            features = speech_array[:max_length]

            def norm(wav, db_level=-27):
                r = 10 ** (db_level / 20)
                a = np.sqrt((len(wav) * (r**2)) / np.sum(wav**2))
                return wav * a

            features = norm(features)

            onnx_outputs = session.run(
                None, {session.get_inputs()[0].name: [features]}
            )[0].squeeze()
            decoded = ctc_beam_search_decoder_for_wav2vec2am(
                onnx_outputs,
                am_alphabet,
                beam_size=beam_width,
                scorer=scorer,
                blank_id=0,
                ignored_symbols=[1, 2, 3],
            )[0].transcript.strip()

            queue_out.put(
                {
                    "wav": filename,
                    "prediction": decoded,
                    "ground_truth": msg["transcript"],
                }
            )
        except FileNotFoundError as ex:
            print("FileNotFoundError: ", ex)

        print(queue_out.qsize(), end="\r")  # Update the current progress
        queue_in.task_done()


def main():
    args = parse_args()
    manager = Manager()
    work_todo = JoinableQueue()  # this is where we are going to store input data
    work_done = manager.Queue()  # this where we are gonna push them out

    processes = []
    for i in range(args.proc):
        worker_process = Process(
            target=evaluation_worker,
            args=(args.model, args.scorer, work_todo, work_done, args.beam_width),
            daemon=True,
            name="evaluate_process_{}".format(i),
        )
        worker_process.start()  # Launch reader() as a separate python process
        processes.append(worker_process)

    wavlist = []
    ground_truths = []
    predictions = []
    losses = []

    with open(args.csv, "r") as csvfile:
        csvreader = csv.DictReader(csvfile)
        count = 0
        for row in csvreader:
            count += 1
            # Relative paths are relative to the folder the CSV file is in
            if not os.path.isabs(row["wav_filename"]):
                row["wav_filename"] = os.path.join(
                    os.path.dirname(args.csv), row["wav_filename"]
                )
            work_todo.put(
                {"filename": row["wav_filename"], "transcript": row["transcript"]}
            )

    print("%d wav entries found in csv" % count)
    work_todo.join()
    print("%d wav file transcribed" % work_done.qsize())

    while not work_done.empty():
        msg = work_done.get()
        losses.append(0.0)
        ground_truths.append(msg["ground_truth"])
        predictions.append(msg["prediction"])
        wavlist.append(msg["wav"])

    # Print test summary
    _ = calculate_and_print_report(
        wavlist, ground_truths, predictions, losses, args.csv
    )

    if args.dump:
        with open(args.dump + ".txt", "w") as ftxt, open(
            args.dump + ".out", "w"
        ) as fout:
            for wav, txt, out in zip(wavlist, ground_truths, predictions):
                ftxt.write("%s %s\n" % (wav, txt))
                fout.write("%s %s\n" % (wav, out))
            print("Reference texts dumped to %s.txt" % args.dump)
            print("Transcription   dumped to %s.out" % args.dump)


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
    try:
        task = Task.init(project_name=args.clearml_project, task_name=args.clearml_task)
    except:
        pass
    return args


if __name__ == "__main__":
    main()
