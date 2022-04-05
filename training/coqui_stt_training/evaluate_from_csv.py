#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import argparse

import pandas as pd
from tqdm import tqdm

from clearml import Task
from coqui_stt_training.util.evaluate_tools import calculate_and_print_report


def evaluate_from_csv(
    transcriptions_csv,
    ground_truth_csv,
    audio_path_trans_column="wav_filename",
    audio_path_gt_column="wav_filename",
    text_trans_column="transcript",
    transcription_gt_column="transcript",
):
    # load csvs
    df_gt = pd.read_csv(ground_truth_csv, sep=",")
    df_transcriptions = pd.read_csv(transcriptions_csv, sep=",")

    # guarantee that text column is different
    df_gt.rename(columns={transcription_gt_column: "transcription_gt"}, inplace=True)
    # guarantee that audio column is equal
    df_gt.rename(columns={audio_path_gt_column: audio_path_trans_column}, inplace=True)

    # the model batch can generate duplicates lines so, dropout all duplicates
    df_gt.drop_duplicates(audio_path_trans_column, inplace=True)
    df_transcriptions.drop_duplicates(audio_path_trans_column, inplace=True)

    # sort to guarantee the same order
    df_gt = df_gt.sort_values(by=[audio_path_trans_column])
    df_transcriptions = df_transcriptions.sort_values(by=[audio_path_trans_column])

    # check if have all files in df_transcriptions
    if len(df_transcriptions.values.tolist()) != len(df_gt.values.tolist()):
        return "ERROR: The following audios are missing in your CSV file: " + str(
            set(df_gt[audio_path_trans_column].values.tolist())
            - set(df_transcriptions[audio_path_trans_column].values.tolist())
        )

    # dropall except the audio and text key for transcription df
    df_transcriptions = df_transcriptions.filter(
        [audio_path_trans_column, text_trans_column]
    )

    # merge dataframes
    df_merged = pd.merge(df_gt, df_transcriptions, on=audio_path_trans_column)

    wav_filenames = []
    ground_truths = []
    predictions = []
    losses = []
    for index, line in tqdm(df_merged.iterrows()):
        # if pred text is None replace for nothing
        if pd.isna(line[text_trans_column]):
            line[text_trans_column] = ""
        # if GT text is None just ignore the sample
        if pd.isna(line["transcription_gt"]):
            continue

        prediction = line[text_trans_column]
        ground_truth = line["transcription_gt"]
        wav_filename = line[audio_path_trans_column]

        wav_filenames.append(wav_filename)
        ground_truths.append(ground_truth)
        predictions.append(prediction)
        losses.append(0.0)

    # Print test summary
    samples = calculate_and_print_report(
        wav_filenames, ground_truths, predictions, losses, transcriptions_csv
    )

    return samples


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Evaluation report using transcription CSV"
    )
    parser.add_argument(
        "--transcriptions_csv",
        type=str,
        help="Path to the CSV transcriptions file.",
    )
    parser.add_argument(
        "--ground_truth_csv",
        type=str,
        help="Path to the CSV source file.",
    )
    parser.add_argument(
        "--clearml_task",
        type=str,
        help="The Experiment name (Task Name) for the ClearML.",
    )

    parser.add_argument(
        "--clearml_project",
        type=str,
        default="STT-Evaluation",
        help="Project Name for the ClearML. Default: STT-Evaluation",
    )

    args = parser.parse_args()

    # init ClearML
    run = Task.init(project_name=args.clearml_project, task_name=args.clearml_task)

    evaluate_from_csv(args.transcriptions_csv, args.ground_truth_csv)
