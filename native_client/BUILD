# Description: Coqui STT native client library.

load("@bazel_skylib//rules:common_settings.bzl", "string_flag")
load("@org_tensorflow//tensorflow:tensorflow.bzl", "lrt_if_needed")
load("@com_github_nelhage_rules_boost//:boost/boost.bzl", "boost_deps")
load("@build_bazel_rules_apple//apple:ios.bzl", "ios_static_framework")
load("@build_bazel_rules_swift//swift:swift.bzl", "swift_c_module", "swift_library")
load("@emsdk//emscripten_toolchain:wasm_rules.bzl", "wasm_cc_binary")


# Only required until https://github.com/emscripten-core/emsdk/pull/1060
# gets merged. Once that's done, we could use "@platform//cpu:wasm32".
config_setting(
    name = "wasm_cpu",
    values = {"cpu": "wasm"},
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

cc_library(
    name = "kenlm_static",
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
)

cc_binary(
    name = "libkenlm.so",
    deps = [":kenlm_static"],
    linkopts = select({
        "//tensorflow:ios": [
            "-fembed-bitcode",
            "-Wl,-install_name,@rpath/libkenlm.so",
        ],
        "//tensorflow:macos": [
            "-Wl,-install_name,@rpath/libkenlm.so",
        ],
        "//tensorflow:windows": [],
        "//conditions:default": [
            "-Wl,-rpath,$$ORIGIN/",
            "-Wl,-soname,libkenlm.so",
        ],
    }),
    linkshared = 1,
)

cc_import(
    name = "kenlm_import",
    shared_library = ":libkenlm.so",
    tags = ["manual"],
)

cc_library(
    name = "kenlm_lib",
    hdrs = glob([
        "kenlm/lm/*.hh",
        "kenlm/util/*.hh",
    ]),
    deps = select({
        # This needs to be linked statically when using WASM/Emscripten.
        # This has licensing implications since KenLM is LGPL.
        ":wasm_cpu": [":kenlm_static"],
        # If not using emscripten, use dynamic linking.
        "//conditions:default": [":kenlm_import"],
    }),
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
    deps = [":kenlm_lib"],
)

cc_library(
    name = "decoder",
    srcs = DECODER_SOURCES,
    includes = DECODER_INCLUDES,
    deps = [":kenlm_lib", ":flashlight"],
    linkopts = DECODER_LINKOPTS,
    copts = select({
        "//tensorflow:windows": ["/std:c++14"],
        "//conditions:default": ["-std=c++14", "-fexceptions", "-fwrapv"],
    }),
)

cc_library(
    name = "coqui_stt_bundle",
    hdrs = [
        "coqui-stt.h",
    ],
    srcs = [
        "stt.cc",
        "stt_errors.cc",
        "modelstate.cc",
        "modelstate.h",
        "workspace_status.cc",
        "workspace_status.h",
        "tflitemodelstate.h",
        "tflitemodelstate.cc",
    ],
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
        "//tensorflow:linux_armhf": LINUX_LINKOPTS,
        "//tensorflow:linux_aarch64": LINUX_LINKOPTS,
        # Bazel is has too strong opinions about static linking, so it's
        # near impossible to get it to link a DLL against another DLL on Windows.
        # We simply force the linker option manually here as a hacky fix.
        "//tensorflow:windows": [
            "bazel-out/x64_windows-opt/bin/native_client/libkenlm.so.if.lib",
        ],
        "//conditions:default": [],
    }) + DECODER_LINKOPTS,
    includes = DECODER_INCLUDES,
    deps = [
        ":decoder",
        "//tensorflow/lite:framework_experimental",
        "//tensorflow/lite/kernels:builtin_ops",
        "//tensorflow/lite/tools/delegates:delegate_provider_lib",
        "//tensorflow/lite/tools/evaluation:utils",
    ],
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

swift_c_module(
    name = "stt_swift_native",
    module_name = "STTNative",
    module_map = "swift.modulemap",
    deps = [":coqui_stt_bundle"],
)

swift_library(
    name = "stt_swift",
    deps = [":stt_swift_native"],
    module_name = "STT",
    srcs = [
        "swift/Bindings.swift",
    ],
)

ios_static_framework(
    name = "stt_ios",
    bundle_name = "STT",
    hdrs = ["coqui-stt.h"],
    deps = [":coqui_stt_bundle"],
    families = ["iphone", "ipad"],
    minimum_os_version = "9.0",
    linkopts = ["-lstdc++"],
)

ios_static_framework(
    name = "kenlm_ios",
    bundle_name = "KenLM",
    deps = [":kenlm_static"],
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
        "@com_google_absl//absl/flags:flag",
        "@com_google_absl//absl/flags:parse",
        "@com_google_absl//absl/types:optional",
        "@boost//:program_options",
    ],
    linkstatic = 1,
    linkopts = select({
        # ARMv7: error: Android 5.0 and later only support position-independent executables (-fPIE).
        "//tensorflow:android": ["-fPIE -pie"],
        # Bazel is has too strong opinions about static linking, so it's
        # near impossible to get it to link a DLL against another DLL on Windows.
        # We simply force the linker option manually here as a hacky fix.
        "//tensorflow:windows": ["bazel-out/x64_windows-opt/bin/native_client/libkenlm.so.if.lib"],
        "//conditions:default": [
            "-lm",
            "-ldl",
            "-pthread",
            "-Wl,-rpath,$$ORIGIN/",
        ],
    }),
)

cc_binary(
    name = "enumerate_kenlm_vocabulary",
    srcs = [
        "enumerate_kenlm_vocabulary.cpp",
    ],
    deps = [":kenlm_lib"],
    copts = select({
        "//tensorflow:windows": ["/std:c++14"],
        "//conditions:default": ["-std=c++14"],
    }),
)

cc_binary(
    name = "trie_load",
    srcs = [
        "trie_load.cc",
    ],
    deps = [":decoder"],
    copts = select({
        "//tensorflow:windows": ["/std:c++14"],
        "//conditions:default": ["-std=c++14"],
    }),
    linkopts = DECODER_LINKOPTS,
)

DECODER_LINKOPTS_WASM = DECODER_LINKOPTS + [
    "-Os",
    "--bind",
    "-sWASM=1",
    # Allow to grow memory allocation when needed (for example for loading models).
    "-sALLOW_MEMORY_GROWTH",
    "-sMAXIMUM_MEMORY=4GB",
    "-sMALLOC=emmalloc",
    "-sMODULARIZE=1",
    "-sEXPORT_NAME=STT",
    # We need to specify a threadpool size, otherwise TFLite will just do nothing
    # and deadlock.
    "-sPTHREAD_POOL_SIZE=4",
    # This is a library, so no 'main' is expected.
    "--no-entry",
    # Experiencing problems? Uncomment the flags below to have better
    # error messages and sanity checks.
    # "-sASSERTIONS=2",
    # "-g3",
    # "-gsource-map",
]

string_flag(name = "wasm_emit", build_setting_default = "wasm_es5")

config_setting(
    name = "wasm_es6",
    flag_values = {
        ":wasm_emit": "es6",
    }
)

cc_binary(
    # Note that the .js suffix is significant here. See the `-o`
    # option at https://emscripten.org/docs/tools_reference/emcc.html
    name = "stt_wasm.js",
    srcs = [
        "wasm/bindings.cc",
    ],
    deps = [":decoder", ":coqui_stt_bundle"],
    copts = ["-std=c++14", "-fno-exceptions", "-fwrapv", "-pthread"],
    linkopts = select({
        ":wasm_es6": DECODER_LINKOPTS_WASM + [
            "-sEXPORT_ES6=1",
            ],
        "//conditions:default": DECODER_LINKOPTS_WASM,
    }),
)

wasm_cc_binary(
    name = "stt_wasm_bindings",
    cc_target = ":stt_wasm.js",
    simd = True,
)
