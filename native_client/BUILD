# Description: Coqui STT native client library.

load(":native_client.bzl", "stt_cc_shared_object")
load("@org_tensorflow//tensorflow:tensorflow.bzl", "tf_copts", "lrt_if_needed")
load("@local_config_cuda//cuda:build_defs.bzl", "if_cuda")
load("@com_github_nelhage_rules_boost//:boost/boost.bzl", "boost_deps")
load("@build_bazel_rules_apple//apple:ios.bzl", "ios_static_framework")

load(
    "@org_tensorflow//tensorflow/lite:build_def.bzl",
    "tflite_copts",
    "tflite_linkopts",
)

config_setting(
    name = "tflite",
    define_values = {
        "runtime": "tflite",
    },
)

config_setting(
    name = "rpi3",
    define_values = {
        "target_system": "rpi3"
    },
)

config_setting(
    name = "rpi3-armv8",
    define_values = {
        "target_system": "rpi3-armv8"
    },
)

genrule(
    name = "workspace_status",
    outs = ["workspace_status.cc"],
    cmd = "$(location :gen_workspace_status.sh) >$@",
    local = 1,
    stamp = 1,
    tools = [":gen_workspace_status.sh"],
)


OPENFST_SOURCES_PLATFORM = select({
    "@org_tensorflow//tensorflow:windows": glob(["ctcdecode/third_party/openfst-1.6.9-win/src/lib/*.cc"]),
    "//conditions:default": glob(["ctcdecode/third_party/openfst-1.6.7/src/lib/*.cc"]),
})

OPENFST_INCLUDES_PLATFORM = select({
    "@org_tensorflow//tensorflow:windows": ["ctcdecode/third_party/openfst-1.6.9-win/src/include"],
    "//conditions:default": ["ctcdecode/third_party/openfst-1.6.7/src/include"],
})

LINUX_LINKOPTS = [
    "-lm",
    "-ldl",
    "-pthread",
    "-Wl,-Bsymbolic",
    "-Wl,-Bsymbolic-functions",
    "-Wl,-export-dynamic",
]

stt_cc_shared_object(
    name = "kenlm",
    hdrs = glob([
        "kenlm/lm/*.hh",
        "kenlm/util/*.hh",
    ]),
    srcs = glob([
        "kenlm/lm/*.cc",
        "kenlm/util/*.cc",
        "kenlm/util/double-conversion/*.cc",
        "kenlm/util/double-conversion/*.h",
    ],
    exclude = [
        "kenlm/*/*test.cc",
        "kenlm/*/*main.cc",
    ],),
    copts = ["-std=c++11"],
    includes = ["kenlm"],
)

DECODER_SOURCES = [
    "alphabet.h",
    "alphabet.cc",
    "ctcdecode/ctc_beam_search_decoder.h",
    "ctcdecode/ctc_beam_search_decoder.cpp",
    "ctcdecode/decoder_utils.h",
    "ctcdecode/decoder_utils.cpp",
    "ctcdecode/path_trie.h",
    "ctcdecode/path_trie.cpp",
    "ctcdecode/scorer.h",
    "ctcdecode/scorer.cpp",
] + OPENFST_SOURCES_PLATFORM

DECODER_INCLUDES = [
    ".",
    "ctcdecode/third_party/ThreadPool",
    "ctcdecode/third_party/object_pool",
    "kenlm",
] + OPENFST_INCLUDES_PLATFORM

cc_library(
    name = "coqui_stt_bundle",
    srcs = [
        "stt.cc",
        "coqui-stt.h",
        "stt_errors.cc",
        "modelstate.cc",
        "modelstate.h",
        "workspace_status.cc",
        "workspace_status.h",
    ] + select({
        "//native_client:tflite": [
            "tflitemodelstate.h",
            "tflitemodelstate.cc",
        ],
        "//conditions:default": [
            "tfmodelstate.h",
            "tfmodelstate.cc",
        ],
    }) + DECODER_SOURCES,
    includes = DECODER_INCLUDES,
    copts = tf_copts() + select({
        # -fvisibility=hidden is not required on Windows, MSCV hides all declarations by default
        "@org_tensorflow//tensorflow:windows": ["/w"],
        # -Wno-sign-compare to silent a lot of warnings from tensorflow itself,
        # which makes it harder to see our own warnings
        "//conditions:default": [
            "-Wno-sign-compare",
            "-fvisibility=hidden",
        ],
    }) + select({
        "//native_client:tflite": ["-DUSE_TFLITE"],
        "//conditions:default": ["-UUSE_TFLITE"],
    }) + tflite_copts(),
    linkopts = lrt_if_needed() + select({
        "@org_tensorflow//tensorflow:macos": [],
        "@org_tensorflow//tensorflow:ios": ["-fembed-bitcode"],
        "@org_tensorflow//tensorflow:linux_x86_64": LINUX_LINKOPTS,
        "//native_client:rpi3": LINUX_LINKOPTS,
        "//native_client:rpi3-armv8": LINUX_LINKOPTS,
        "@org_tensorflow//tensorflow:windows": [],
        "//conditions:default": [],
    }) + tflite_linkopts(),
    deps = select({
        "//native_client:tflite": [
            "@org_tensorflow//tensorflow/lite/kernels:builtin_ops",
            "@org_tensorflow//tensorflow/lite/tools/evaluation:utils",
        ],
        "//conditions:default": [
            "@org_tensorflow//tensorflow/core:core_cpu",
            "@org_tensorflow//tensorflow/core:direct_session",
            "@org_tensorflow//third_party/eigen3",
            #"//tensorflow/core:all_kernels",
            ### => Trying to be more fine-grained
            ### Use bin/ops_in_graph.py to list all the ops used by a frozen graph.
            ### CPU only build, libstt.so file size reduced by ~50%
            "@org_tensorflow//tensorflow/core/kernels:spectrogram_op",  # AudioSpectrogram
            "@org_tensorflow//tensorflow/core/kernels:bias_op",  # BiasAdd
            "@org_tensorflow//tensorflow/core/kernels:cast_op",  # Cast
            "@org_tensorflow//tensorflow/core/kernels:concat_op",  # ConcatV2
            "@org_tensorflow//tensorflow/core/kernels:constant_op",  # Const, Placeholder
            "@org_tensorflow//tensorflow/core/kernels:shape_ops",  # ExpandDims, Shape
            "@org_tensorflow//tensorflow/core/kernels:gather_nd_op",  # GatherNd
            "@org_tensorflow//tensorflow/core/kernels:identity_op",  # Identity
            "@org_tensorflow//tensorflow/core/kernels:immutable_constant_op",  # ImmutableConst (used in memmapped models)
            "@org_tensorflow//tensorflow/core/kernels:deepspeech_cwise_ops",  # Less, Minimum, Mul
            "@org_tensorflow//tensorflow/core/kernels:matmul_op",  # MatMul
            "@org_tensorflow//tensorflow/core/kernels:reduction_ops",  # Max
            "@org_tensorflow//tensorflow/core/kernels:mfcc_op",  # Mfcc
            "@org_tensorflow//tensorflow/core/kernels:no_op",  # NoOp
            "@org_tensorflow//tensorflow/core/kernels:pack_op",  # Pack
            "@org_tensorflow//tensorflow/core/kernels:sequence_ops",  # Range
            "@org_tensorflow//tensorflow/core/kernels:relu_op",  # Relu
            "@org_tensorflow//tensorflow/core/kernels:reshape_op",  # Reshape
            "@org_tensorflow//tensorflow/core/kernels:softmax_op",  # Softmax
            "@org_tensorflow//tensorflow/core/kernels:tile_ops",  # Tile
            "@org_tensorflow//tensorflow/core/kernels:transpose_op",  # Transpose
            "@org_tensorflow//tensorflow/core/kernels:rnn_ops",  # BlockLSTM
            # And we also need the op libs for these ops used in the model:
            "@org_tensorflow//tensorflow/core:audio_ops_op_lib",  # AudioSpectrogram, Mfcc
            "@org_tensorflow//tensorflow/core:rnn_ops_op_lib",  # BlockLSTM
            "@org_tensorflow//tensorflow/core:math_ops_op_lib",  # Cast, Less, Max, MatMul, Minimum, Range
            "@org_tensorflow//tensorflow/core:array_ops_op_lib",  # ConcatV2, Const, ExpandDims, Fill, GatherNd, Identity, Pack, Placeholder, Reshape, Tile, Transpose
            "@org_tensorflow//tensorflow/core:no_op_op_lib",  # NoOp
            "@org_tensorflow//tensorflow/core:nn_ops_op_lib",  # Relu, Softmax, BiasAdd
            # And op libs for these ops brought in by dependencies of dependencies to silence unknown OpKernel warnings:
            "@org_tensorflow//tensorflow/core:dataset_ops_op_lib",  # UnwrapDatasetVariant, WrapDatasetVariant
            "@org_tensorflow//tensorflow/core:sendrecv_ops_op_lib",  # _HostRecv, _HostSend, _Recv, _Send
        ],
    }) + if_cuda([
        "@org_tensorflow//tensorflow/core:core",
    ]) + [":kenlm_import"],
)

stt_cc_shared_object(
    name = "stt",
    deps = [":coqui_stt_bundle"],
)

ios_static_framework(
    name = "stt_ios",
    deps = [":coqui_stt_bundle"],
    families = ["iphone", "ipad"],
    minimum_os_version = "9.0",
    linkopts = ["-lstdc++"],
)

genrule(
    name = "libstt_so_dsym",
    srcs = [":libstt.so"],
    outs = ["libstt.so.dSYM"],
    output_to_bindir = True,
    cmd = "dsymutil $(location :libstt.so) -o $@"
)

cc_binary(
    name = "generate_scorer_package",
    srcs = [
        "generate_scorer_package.cpp",
        "stt_errors.cc",
    ] + DECODER_SOURCES,
    copts = ["-std=c++11"],
    deps = [
        "@com_google_absl//absl/flags:flag",
        "@com_google_absl//absl/flags:parse",
        "@com_google_absl//absl/types:optional",
        "@boost//:program_options",
    ],
    linkstatic = 1,
    linkopts = LINUX_LINKOPTS + select({
        # ARMv7: error: Android 5.0 and later only support position-independent executables (-fPIE).
        "@org_tensorflow//tensorflow:android": ["-fPIE -pie"],
        "//conditions:default": [],
    }),
    includes = DECODER_INCLUDES,
)

cc_binary(
    name = "enumerate_kenlm_vocabulary",
    srcs = [
        "enumerate_kenlm_vocabulary.cpp",
    ],
    deps = [":kenlm"],
    copts = ["-std=c++11"],
)

cc_binary(
    name = "trie_load",
    srcs = [
        "alphabet.h",
        "trie_load.cc",
    ],
    copts = ["-std=c++11"],
    deps = [":decoder"],
)
