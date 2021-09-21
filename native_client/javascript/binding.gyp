{
    "targets": [
        {
            "target_name": "stt",
            "sources": ["stt_wrap.cxx"],
            "libraries": [],
            "include_dirs": ["../"],
            "conditions": [
                [
                    "OS=='mac'",
                    {
                        "xcode_settings": {
                            "OTHER_CXXFLAGS": [
                                "-stdlib=libc++",
                                "-mmacosx-version-min=10.10",
                            ],
                            "OTHER_LDFLAGS": [
                                "-stdlib=libc++",
                                "-mmacosx-version-min=10.10",
                            ],
                        }
                    },
                ],
                [
                    "OS=='win'",
                    {
                        "libraries": [
                            "../../../tensorflow/bazel-bin/native_client/libstt.so.if.lib",
                            "../../../tensorflow/bazel-bin/native_client/libkenlm.so.if.lib",
                            "../../../tensorflow/bazel-bin/native_client/libtflitedelegates.so.if.lib",
                            "../../../tensorflow/bazel-bin/tensorflow/lite/libtensorflowlite.so.if.lib",
                        ],
                    },
                    {
                        "libraries": [
                            "../../../tensorflow/bazel-bin/native_client/libstt.so",
                            "../../../tensorflow/bazel-bin/native_client/libkenlm.so",
                            "../../../tensorflow/bazel-bin/native_client/libtflitedelegates.so",
                            "../../../tensorflow/bazel-bin/tensorflow/lite/libtensorflowlite.so",
                        ],
                    },
                ],
            ],
        },
        {
            "target_name": "action_after_build",
            "type": "none",
            "dependencies": ["<(module_name)"],
            "copies": [
                {
                    "files": ["<(PRODUCT_DIR)/<(module_name).node"],
                    "destination": "<(module_path)",
                }
            ],
        },
    ],
    "variables": {
        "build_v8_with_gn": 0,
        "v8_enable_pointer_compression": 0,
        "v8_enable_31bit_smis_on_64bit_arch": 0,
        "enable_lto": 1,
    },
}
