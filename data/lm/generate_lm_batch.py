import argparse
import gzip
import io
import os
import re
import subprocess
import logging
from collections import Counter
import datetime, time

import concurrent.futures
from concurrent.futures import wait

import progressbar
from clearml import Task

from generate_lm import build_lm, convert_and_filter_topk
from coqui_stt_training.util import cpu

logging.basicConfig(level=logging.INFO)


def generate_batch_lm(parser_batch, arpa_order, top_k, arpa_prune, i, total_runs):
    # Create a child parser and add single elements
    parser_single = argparse.ArgumentParser(
        parents=[parser_batch],
        add_help=False,
    )
    parser_single.add_argument("--arpa_order", type=int, default=arpa_order)
    parser_single.add_argument("--top_k", type=int, default=top_k)
    parser_single.add_argument("--arpa_prune", type=str, default=arpa_prune)
    args_single = parser_single.parse_args()
    _start_time = (
        time.perf_counter()
    )  # We use time.perf_counter() to acurately mesure delta of t; not datetime obj nor standard time.time()
    logging.info("-" * 3 * 10)
    logging.info(
        f"{float(time.perf_counter() - _start_time)} seconds RUNNING {i}/{total_runs} FOR {arpa_order=} {top_k=} {arpa_prune=}"
    )
    logging.info("-" * 3 * 10)
    # call with these arguments
    data_lower, vocab_str = convert_and_filter_topk(args_single)
    build_lm(args_single, data_lower, vocab_str)
    parser_single = None
    os.remove(os.path.join(args_single.output_dir, "lm.arpa"))
    os.remove(os.path.join(args_single.output_dir, "lm_filtered.arpa"))
    print(f"LM generation {i} took: {time.perf_counter() - _start_time}")


def parse_args():
    n = int(cpu.available_count())
    parser_batch = argparse.ArgumentParser(
        description="Generate lm.binary and top-k vocab for Coqui STT in batch for multiple arpa_order, top_k and arpa_prune values."
    )
    parser_batch.add_argument(
        "--input_txt",
        help="Path to a file.txt or file.txt.gz with sample sentences",
        type=str,
        required=True,
    )
    parser_batch.add_argument(
        "--output_dir", help="Directory path for the output", type=str, required=True
    )
    # parser.add_argument(
    #     "--top_k",
    #     help="Use top_k most frequent words for the vocab.txt file. These will be used to filter the ARPA file.",
    #     type=int,
    #     required=False,
    # )
    parser_batch.add_argument(
        "--kenlm_bins",
        help="File path to the KENLM binaries lmplz, filter and build_binary",
        type=str,
        required=True,
    )
    # parser.add_argument(
    #     "--arpa_order",
    #     help="Order of k-grams in ARPA-file generation",
    #     type=int,
    #     required=False,
    # )
    parser_batch.add_argument(
        "--max_arpa_memory",
        help="Maximum allowed memory usage for ARPA-file generation",
        type=str,
        required=True,
    )
    # parser.add_argument(
    #     "--arpa_prune",
    #     help="ARPA pruning parameters. Separate values with '|'",
    #     type=str,
    #     required=True,
    # )
    parser_batch.add_argument(
        "--binary_a_bits",
        help="Build binary quantization value a in bits",
        type=int,
        required=True,
    )
    parser_batch.add_argument(
        "--binary_q_bits",
        help="Build binary quantization value q in bits",
        type=int,
        required=True,
    )
    parser_batch.add_argument(
        "--binary_type",
        help="Build binary data structure type",
        type=str,
        required=True,
    )
    parser_batch.add_argument(
        "--discount_fallback",
        help="To try when such message is returned by kenlm: 'Could not calculate Kneser-Ney discounts [...] rerun with --discount_fallback'",
        action="store_true",
    )
    parser_batch.add_argument(
        "--clearml_project",
        required=False,
        default="STT/wav2vec2 decoding",
    )
    parser_batch.add_argument(
        "--clearml_task",
        required=False,
        default="LM generation",
    )

    #
    # The following are added for batch processing instead of single ones commented out above
    #

    parser_batch.add_argument(
        "--arpa_order_list",
        help="List of arpa_order values. Separate values with '-' (e.g. '3-4-5').",
        type=str,
        required=True,
    )
    parser_batch.add_argument(
        "--top_k_list",
        help="A list of top_k values. Separate values with '-' (e.g. '20000-50000').",
        type=str,
        required=True,
    )
    parser_batch.add_argument(
        "--arpa_prune_list",
        help="ARPA pruning parameters. Separate values with '|', groups with '-' (e.g. '0|0|1-0|0|2')",
        type=str,
        required=True,
    )
    parser_batch.add_argument(
        "-j",
        "--n_proc",
        help=f"Maximum allowed processes. (default: {n})",
        type=int,
        default=n,
    )

    return parser_batch


def main():

    args_batch = parse_args()
    args_parsed_batch = args_batch.parse_args()

    try:
        task = Task.init(
            project_name=args_parsed_batch.clearml_project,
            task_name=args_parsed_batch.clearml_task,
        )
    except Exception:
        pass

    arpa_order_list = []
    top_k_list = []
    for x in args_parsed_batch.arpa_order_list.split("-"):
        if x.isnumeric():
            arpa_order_list.append(int(float(x)))
    for x in args_parsed_batch.top_k_list.split("-"):
        if x.isnumeric():
            top_k_list.append(int(float(x)))
    arpa_prune_list = args_parsed_batch.arpa_prune_list.split("-")

    i = 1
    total_runs = len(arpa_order_list) * len(top_k_list) * len(arpa_prune_list)
    start_time = time.perf_counter()

    assert int(args_parsed_batch.n_proc) <= int(
        total_runs
    ), f"Maximum number of proc exceded given {total_runs} task(s).\n[{args_parsed_batch.n_proc=} <= {total_runs=}]\nSet the -j|--n_proc argument to a value equal or lower than {total_runs}."

    n = int(args_parsed_batch.n_proc)

    with concurrent.futures.ThreadPoolExecutor(max_workers=n) as executor:
        futures = []
        for i, arpa_order in enumerate(arpa_order_list, start=1):
            for top_k in top_k_list:
                for arpa_prune in arpa_prune_list:
                    future = executor.submit(
                        generate_batch_lm,
                        args_batch,
                        arpa_order,
                        top_k,
                        arpa_prune,
                        i,
                        total_runs,
                    )
                    futures.append(future)
                    i += 1
        wait(futures)

    try:
        task.upload_artifact(
            name="lm.binary",
            artifact_object=os.path.join(args_parsed_batch.output_dir, "lm.binary"),
        )
    except Exception:
        pass

    # Delete intermediate files
    os.remove(os.path.join(args_batch.output_dir, "lower.txt.gz"))

    logging.info(
        f"Took {time.perf_counter() - start_time} to generate {total_runs} language {'models' if total_runs > 1 else 'model'}."
    )


if __name__ == "__main__":
    main()
