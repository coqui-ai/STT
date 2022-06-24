import argparse
import gzip
import io
import os
import subprocess
from collections import Counter

import progressbar
from clearml import Task

counter = Counter()

def convert_and_filter_topk(args):
    global counter
    """Convert to lowercase, count word occurrences and save top-k words to a file"""

    # counter = Counter()
    data_lower = os.path.join(args.output_dir, "lower.txt.gz")

    # Skip this phase if lower.txt.gz already exists
    print("\nConverting to lowercase...")
    if os.path.isfile(data_lower):
        print("Already converted, skipping conversion...")
    else:
        with io.TextIOWrapper(
            io.BufferedWriter(gzip.open(data_lower, "w+")), encoding="utf-8"
        ) as file_out:

            # Open the input file either from input.txt or input.txt.gz
            _, file_extension = os.path.splitext(args.input_txt)
            if file_extension == ".gz":
                file_in = io.TextIOWrapper(
                    io.BufferedReader(gzip.open(args.input_txt)), encoding="utf-8"
                )
            else:
                file_in = open(args.input_txt, encoding="utf-8")

            for line in progressbar.progressbar(file_in):
                line_lower = line.lower()
                counter.update(line_lower.split())
                file_out.write(line_lower)

            file_in.close()

    # Save top-k words
    print("\nCounting word occurrences ...")
    vocab_path = "vocab-{}.txt".format(args.top_k)
    vocab_path = os.path.join(args.output_dir, vocab_path)
    top_counter = counter.most_common(args.top_k)
    vocab_str = "\n".join(word for word, count in top_counter)
    # Skip this phase if vocab_path already exists
    if os.path.isfile(vocab_path):
        print("Already calculated for top_k={}, skipping...".format(args.top_k))
    else:
        print("\nSaving top {} words ...".format(args.top_k))
        with open(vocab_path, "w+") as file:
            file.write(vocab_str)

        print("\nCalculating word statistics ...")
        total_words = sum(counter.values())
        print("  Your text file has {} words in total".format(total_words))
        print("  It has {} unique words".format(len(counter)))
        top_words_sum = sum(count for word, count in top_counter)
        word_fraction = (top_words_sum / total_words) * 100
        print(
            "  Your top-{} words are {:.4f} percent of all words".format(
                args.top_k, word_fraction
            )
        )
        print('  Your most common word "{}" occurred {} times'.format(*top_counter[0]))
        last_word, last_count = top_counter[-1]
        print(
            '  The least common word in your top-k is "{}" with {} times'.format(
                last_word, last_count
            )
        )
        for i, (w, c) in enumerate(reversed(top_counter)):
            if c > last_count:
                print(
                    '  The first word with {} occurrences is "{}" at place {}'.format(
                        c, w, len(top_counter) - 1 - i
                    )
                )
                break

    return data_lower, vocab_str


def build_lm(args, data_lower, vocab_str):
    print("\nCreating ARPA file ...")
    lm_path = os.path.join(args.output_dir, "lm.arpa")
    subargs = [
        os.path.join(args.kenlm_bins, "lmplz"),
        "--order",
        str(args.arpa_order),
        "--temp_prefix",
        args.output_dir,
        "--memory",
        args.max_arpa_memory,
        "--text",
        data_lower,
        "--arpa",
        lm_path,
        "--prune",
        *args.arpa_prune.split("|"),
    ]
    if args.discount_fallback:
        subargs += ["--discount_fallback"]
    subprocess.check_call(subargs)

    # Filter LM using vocabulary of top-k words
    print("\nFiltering ARPA file using vocabulary of top-k words ...")
    filtered_path = os.path.join(args.output_dir, "lm_filtered.arpa")
    subprocess.run(
        [
            os.path.join(args.kenlm_bins, "filter"),
            "single",
            "model:{}".format(lm_path),
            filtered_path,
        ],
        input=vocab_str.encode("utf-8"),
        check=True,
    )

    # Quantize and produce trie binary.
    print("\nBuilding lm.binary ...")
    binary_path = os.path.join(
        args.output_dir,
        "lm_{}_{}_{}.binary".format(
            str(args.arpa_order),
            str(args.top_k),
            str(args.arpa_prune.replace("|",""))
            )
    )
    subprocess.check_call(
        [
            os.path.join(args.kenlm_bins, "build_binary"),
            "-a",
            str(args.binary_a_bits),
            "-q",
            str(args.binary_q_bits),
            "-v",
            args.binary_type,
            filtered_path,
            binary_path,
        ]
    )


def main():
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


    args_batch = parser_batch.parse_args()
    # print("ARGS_BATCH = ",args_batch)

    # try:
    #     task = Task.init(project_name=args_batch.clearml_project, task_name=args_batch.clearml_task)
    # except:
    #     pass

    top_k_list = [int(x) for x in args_batch.top_k_list.split("-")]
    arpa_order_list = [int(x) for x in args_batch.arpa_order_list.split("-")]
    arpa_prune_list = args_batch.arpa_prune_list.split("-")

    for arpa_order in arpa_order_list:
        for top_k in top_k_list:
            for arpa_prune in arpa_prune_list:
                # Create a child parser and add single elements
                parser_single = argparse.ArgumentParser(
                    parents=[parser_batch],
                    add_help=False,
                )
                parser_single.add_argument("--arpa_order", type=int, default=arpa_order, )
                parser_single.add_argument("--top_k", type=int, default=top_k, )
                parser_single.add_argument("--arpa_prune", type=str, default=arpa_prune,)
                args_single = parser_single.parse_args()
                print('---------------------------------------------------------------------------------------------')
                print("RUNNING FOR arpa_order={} top_k={} arpa_prune={}".format(str(arpa_order), str(top_k), arpa_prune))
                print('---------------------------------------------------------------------------------------------')
                # call with these arguments
                data_lower, vocab_str = convert_and_filter_topk(args_single)
                build_lm(args_single, data_lower, vocab_str)
                parser_single = None

    # try:
    #     task.upload_artifact(
    #         name="lm.binary", artifact_object=os.path.join(args.output_dir, "lm.binary")
    #     )
    # except:
    #     pass

    # Delete intermediate files
    os.remove(os.path.join(args_batch.output_dir, "lower.txt.gz"))
    os.remove(os.path.join(args_batch.output_dir, "lm.arpa"))
    os.remove(os.path.join(args_batch.output_dir, "lm_filtered.arpa"))

if __name__ == "__main__":
    main()
