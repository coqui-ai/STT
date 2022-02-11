# Description: Coqui STT native client library.

load("@org_tensorflow//tensorflow:tensorflow.bzl", "lrt_if_needed")
load("@com_github_nelhage_rules_boost//:boost/boost.bzl", "boost_deps")
load("@build_bazel_rules_apple//apple:ios.bzl", "ios_static_framework")


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
    "//tensorflow:windows": glob(["ctcdecode/third_party/openfst-1.6.9-win/src/lib/*.cc"]),
    "//conditions:default": glob(["ctcdecode/third_party/openfst-1.6.7/src/lib/*.cc"]),
})

OPENFST_INCLUDES_PLATFORM = select({
    "//tensorflow:windows": ["ctcdecode/third_party/openfst-1.6.9-win/src/include"],
    "//conditions:default": ["ctcdecode/third_party/openfst-1.6.7/src/include"],
})

DECODER_SOURCES = [
    "alphabet.cc",
    "alphabet.h",
    "ctcdecode/ctc_beam_search_decoder.cpp",
    "ctcdecode/ctc_beam_search_decoder.h",
    "ctcdecode/decoder_utils.cpp",
    "ctcdecode/decoder_utils.h",
    "ctcdecode/path_trie.cpp",
    "ctcdecode/path_trie.h",
    "ctcdecode/scorer.cpp",
    "ctcdecode/scorer.h",
] + OPENFST_SOURCES_PLATFORM

DECODER_INCLUDES = [
    ".",
    "ctcdecode/third_party/ThreadPool",
    "ctcdecode/third_party/object_pool",
] + OPENFST_INCLUDES_PLATFORM

DECODER_LINKOPTS = [
    "-lm",
    "-ldl",
    "-pthread",
]

LINUX_LINKOPTS = [
    "-ldl",
    "-pthread",
    "-Wl,-Bsymbolic",
    "-Wl,-Bsymbolic-functions",
    "-Wl,-export-dynamic",
]

cc_binary(
    name = "libkenlm.so",
    srcs = glob([
        "kenlm/lm/*.hh",
        "kenlm/lm/*.cc",
        "kenlm/util/*.hh",
        "kenlm/util/*.cc",
        "kenlm/util/double-conversion/*.cc",
        "kenlm/util/double-conversion/*.h",
    ],
    exclude = [
        "kenlm/*/*test.cc",
        "kenlm/*/*main.cc",
    ],),
    copts = select({
        "//tensorflow:windows": ["/std:c++14"],
        "//conditions:default": ["-std=c++14", "-fwrapv", "-fvisibility=hidden"],
    }),
    defines = ["KENLM_MAX_ORDER=6"],
    includes = ["kenlm"],
    linkshared = 1,
    linkopts = select({
        "//tensorflow:ios": [
            "-Wl,-install_name,@rpath/libkenlm.so",
        ],
        "//tensorflow:macos": [
            "-Wl,-install_name,@rpath/libkenlm.so",
        ],
        "//tensorflow:windows": [],
        "//conditions:default": [
            "-Wl,-soname,libkenlm.so",
        ],
    }),
)

cc_library(
    name="kenlm",
    hdrs = glob([
        "kenlm/lm/*.hh",
        "kenlm/util/*.hh",
    ]),
    srcs = [":libkenlm.so"],
    copts = ["-std=c++14"],
    defines = ["KENLM_MAX_ORDER=6"],
    includes = [".", "kenlm"],
)

cc_library(
    name = "flashlight",
    hdrs = [
        "ctcdecode/third_party/flashlight/flashlight/lib/common/String.h",
        "ctcdecode/third_party/flashlight/flashlight/lib/common/System.h",
        "ctcdecode/third_party/flashlight/flashlight/lib/text/decoder/Decoder.h",
        "ctcdecode/third_party/flashlight/flashlight/lib/text/decoder/LexiconDecoder.h",
        "ctcdecode/third_party/flashlight/flashlight/lib/text/decoder/LexiconFreeDecoder.h",
        "ctcdecode/third_party/flashlight/flashlight/lib/text/decoder/lm/ConvLM.h",
        "ctcdecode/third_party/flashlight/flashlight/lib/text/decoder/lm/KenLM.h",
        "ctcdecode/third_party/flashlight/flashlight/lib/text/decoder/lm/LM.h",
        "ctcdecode/third_party/flashlight/flashlight/lib/text/decoder/lm/ZeroLM.h",
        "ctcdecode/third_party/flashlight/flashlight/lib/text/decoder/Trie.h",
        "ctcdecode/third_party/flashlight/flashlight/lib/text/decoder/Utils.h",
        "ctcdecode/third_party/flashlight/flashlight/lib/text/dictionary/Defines.h",
        "ctcdecode/third_party/flashlight/flashlight/lib/text/dictionary/Dictionary.h",
        "ctcdecode/third_party/flashlight/flashlight/lib/text/dictionary/Utils.h",
    ],
    srcs = [
        "ctcdecode/third_party/flashlight/flashlight/lib/common/String.cpp",
        "ctcdecode/third_party/flashlight/flashlight/lib/common/System.cpp",
        "ctcdecode/third_party/flashlight/flashlight/lib/text/decoder/LexiconDecoder.cpp",
        "ctcdecode/third_party/flashlight/flashlight/lib/text/decoder/LexiconFreeDecoder.cpp",
        "ctcdecode/third_party/flashlight/flashlight/lib/text/decoder/lm/ConvLM.cpp",
        "ctcdecode/third_party/flashlight/flashlight/lib/text/decoder/lm/KenLM.cpp",
        "ctcdecode/third_party/flashlight/flashlight/lib/text/decoder/lm/ZeroLM.cpp",
        "ctcdecode/third_party/flashlight/flashlight/lib/text/decoder/Trie.cpp",
        "ctcdecode/third_party/flashlight/flashlight/lib/text/decoder/Utils.cpp",
        "ctcdecode/third_party/flashlight/flashlight/lib/text/dictionary/Dictionary.cpp",
        "ctcdecode/third_party/flashlight/flashlight/lib/text/dictionary/Utils.cpp",
    ],
    includes = ["ctcdecode/third_party/flashlight"],
    deps = [":kenlm"],
)

cc_library(
    name = "decoder",
    srcs = DECODER_SOURCES,
    includes = DECODER_INCLUDES,
    deps = [":kenlm", ":flashlight"],
    linkopts = DECODER_LINKOPTS,
    copts = select({
        "//tensorflow:windows": ["/std:c++14"],
        "//conditions:default": ["-std=c++14", "-fexceptions", "-fwrapv"],
    }),
)

cc_library(
    name = "tflite",
    hdrs = [
        "//tensorflow/lite:model.h",
        "//tensorflow/lite/kernels:register.h",
    ] + select({
        "//tensorflow:android": [
            "//tensorflow/lite/delegates/gpu:delegate.h",
            "//tensorflow/lite/delegates/hexagon:hexagon_delegate.h",
        ],
        "//conditions:default": [],
    }),
    srcs = [
        "//tensorflow/lite:libtensorflowlite.so",
    ],
    includes = ["tensorflow"],
    deps = ["//tensorflow/lite:libtensorflowlite.so"],
)

cc_binary(
    name = "libtflitedelegates.so",
    deps = [
        "//tensorflow/lite/tools/evaluation:utils",
    ],
    linkshared = 1,
    linkopts = select({
        "//tensorflow:ios": [
            "-Wl,-install_name,@rpath/libtflitedelegates.so",
        ],
        "//tensorflow:macos": [
            "-Wl,-install_name,@rpath/libtflitedelegates.so",
        ],
        "//tensorflow:windows": [],
        "//conditions:default": [
            "-Wl,-soname,libtflitedelegates.so",
        ],
    }),
)

cc_library(
    name = "tflitedelegates",
    hdrs = [
        "//tensorflow/lite/tools/evaluation:utils.h",
    ],
    deps = [
        "//tensorflow/lite/tools/evaluation:utils",
    ],
    srcs = [":libtflitedelegates.so"],
)

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
        "tflitemodelstate.h",
        "tflitemodelstate.cc",
<<<<<<< HEAD
    ] + DECODER_SOURCES,
=======
<<<<<<< HEAD
    ] + DECODER_SOURCES,
=======
    ],
>>>>>>> coqui-ai-main
>>>>>>> 94b13b64c30dd1349c6e325dba22877620ef914b
    copts = select({
        # -fvisibility=hidden is not required on Windows, MSCV hides all declarations by default
        "//tensorflow:windows": ["/std:c++14", "/w"],
        # -Wno-sign-compare to silent a lot of warnings from tensorflow itself,
        # which makes it harder to see our own warnings
        "//conditions:default": [
            "-std=c++14",
            "-fwrapv",
            "-Wno-sign-compare",
            "-fvisibility=hidden",
        ],
    }),
    linkopts = lrt_if_needed() + select({
        "//tensorflow:macos": [],
        "//tensorflow:ios": ["-fembed-bitcode"],
        "//tensorflow:linux_x86_64": LINUX_LINKOPTS,
        "//native_client:rpi3": LINUX_LINKOPTS,
        "//native_client:rpi3-armv8": LINUX_LINKOPTS,
        # Bazel is has too strong opinions about static linking, so it's
        # near impossible to get it to link a DLL against another DLL on Windows.
        # We simply force the linker option manually here as a hacky fix.
        "//tensorflow:windows": [
            "bazel-out/x64_windows-opt/bin/native_client/libkenlm.so.if.lib",
<<<<<<< HEAD
            "bazel-out/x64_windows-opt/bin/native_client/libtflitedelegates.so.if.lib",
            "bazel-out/x64_windows-opt/bin/tensorflow/lite/libtensorflowlite.so.if.lib",
=======
<<<<<<< HEAD
            "bazel-out/x64_windows-opt/bin/native_client/libtflitedelegates.so.if.lib",
            "bazel-out/x64_windows-opt/bin/tensorflow/lite/libtensorflowlite.so.if.lib",
=======
>>>>>>> coqui-ai-main
>>>>>>> 94b13b64c30dd1349c6e325dba22877620ef914b
        ],
        "//conditions:default": [],
    }) + DECODER_LINKOPTS,
    includes = DECODER_INCLUDES,
<<<<<<< HEAD
    deps = [":kenlm", ":tflite", ":tflitedelegates", ":flashlight"],
=======
<<<<<<< HEAD
    deps = [":kenlm", ":tflite", ":tflitedelegates", ":flashlight"],
=======
    deps = [
        ":decoder",
        "//tensorflow/lite:framework_stable",
        "//tensorflow/lite/kernels:builtin_ops",
        "//tensorflow/lite/tools/evaluation:utils",
    ],
>>>>>>> coqui-ai-main
>>>>>>> 94b13b64c30dd1349c6e325dba22877620ef914b
)

cc_binary(
    name = "libstt.so",
    deps = [":coqui_stt_bundle"],
    linkshared = 1,
    linkopts = select({
        "//tensorflow:ios": [
            "-Wl,-install_name,@rpath/libstt.so",
        ],
        "//tensorflow:macos": [
            "-Wl,-install_name,@rpath/libstt.so",
        ],
        "//tensorflow:windows": [],
        "//conditions:default": [
            "-Wl,-soname,libstt.so",
        ],
    }),
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
    ],
    copts = select({
        "//tensorflow:windows": ["/std:c++14"],
        "//conditions:default": ["-std=c++14"],
    }),
    deps = [
        ":decoder",
        ":kenlm",
        "@com_google_absl//absl/flags:flag",
        "@com_google_absl//absl/flags:parse",
        "@com_google_absl//absl/types:optional",
        "@boost//:program_options",
    ],
    linkstatic = 1,
    linkopts = [
        "-lm",
        "-ldl",
        "-pthread",
    ] + select({
        # ARMv7: error: Android 5.0 and later only support position-independent executables (-fPIE).
        "//tensorflow:android": ["-fPIE -pie"],
        # Bazel is has too strong opinions about static linking, so it's
        # near impossible to get it to link a DLL against another DLL on Windows.
        # We simply force the linker option manually here as a hacky fix.
        "//tensorflow:windows": ["bazel-out/x64_windows-opt/bin/native_client/libkenlm.so.if.lib"],
        "//conditions:default": [],
    }),
)

cc_binary(
    name = "enumerate_kenlm_vocabulary",
    srcs = [
        "enumerate_kenlm_vocabulary.cpp",
    ],
    deps = [":kenlm"],
    copts = select({
        "//tensorflow:windows": ["/std:c++14"],
        "//conditions:default": ["-std=c++14"],
    }),
)

cc_binary(
    name = "trie_load",
    srcs = [
        "trie_load.cc",
<<<<<<< HEAD
    ] + DECODER_SOURCES,
=======
<<<<<<< HEAD
    ] + DECODER_SOURCES,
=======
    ],
    deps = [":decoder"],
>>>>>>> coqui-ai-main
>>>>>>> 94b13b64c30dd1349c6e325dba22877620ef914b
    copts = select({
        "//tensorflow:windows": ["/std:c++14"],
        "//conditions:default": ["-std=c++14"],
    }),
    linkopts = DECODER_LINKOPTS,
)
