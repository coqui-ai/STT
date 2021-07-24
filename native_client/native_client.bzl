
# Shared libraries have different name pattern on different platforms,
# but cc_binary cannot output correct artifact name yet,
# so we generate multiple cc_binary targets with all name patterns when necessary.
# TODO: Remove this workaround when cc_shared_library is available on Bazel.
SHARED_LIBRARY_NAME_PATTERNS = [
    "lib%s.so%s",  # On Linux, shared libraries are usually named as libfoo.so
    "lib%s%s.dylib",  # On macos, shared libraries are usually named as libfoo.dylib
    "%s%s.dll",  # On Windows, shared libraries are usually named as foo.dll
]

def stt_cc_shared_object(
        name,
        srcs = [],
        deps = [],
        hdrs = [],
        data = [],
        linkopts = [],
        soversion = None,
        kernels = [],
        per_os_targets = True,
        visibility = None,
        **kwargs):
    if soversion != None:
        suffix = "." + str(soversion).split(".")[0]
        longsuffix = "." + str(soversion)
    else:
        suffix = ""
        longsuffix = ""

    if per_os_targets:
        names = [
            (
                pattern % (name, ""),
                pattern % (name, suffix),
                pattern % (name, longsuffix),
            )
            for pattern in SHARED_LIBRARY_NAME_PATTERNS
        ]
    else:
        names = [(
            name,
            name + suffix,
            name + longsuffix,
        )]

    for name_os, name_os_major, name_os_full in names:
        # Windows DLLs cant be versioned
        if name_os.endswith(".dll"):
            name_os_major = name_os
            name_os_full = name_os

        if name_os != name_os_major:
            native.genrule(
                name = name_os + "_sym",
                outs = [name_os],
                srcs = [name_os_major],
                output_to_bindir = 1,
                cmd = "ln -sf $$(basename $<) $@",
            )
            native.genrule(
                name = name_os_major + "_sym",
                outs = [name_os_major],
                srcs = [name_os_full],
                output_to_bindir = 1,
                cmd = "ln -sf $$(basename $<) $@",
            )

        soname = name_os_major.split("/")[-1]

        native.cc_binary(
            name = name_os_full,
            srcs = srcs + hdrs,
            deps = deps,
            linkshared = 1,
            data = data,
            linkopts = linkopts + select({
                "@org_tensorflow//tensorflow:ios": [
                    "-Wl,-install_name,@rpath/" + soname,
                ],
                "@org_tensorflow//tensorflow:macos": [
                    "-Wl,-install_name,@rpath/" + soname,
                ],
                "@org_tensorflow//tensorflow:windows": [],
                "//conditions:default": [
                    "-Wl,-soname," + soname,
                ],
            }),
            visibility = visibility,
            **kwargs
        )

    flat_names = [item for sublist in names for item in sublist]
    if name not in flat_names:
        native.cc_import(
            name = name + "_import",
            shared_library = select({
                "@org_tensorflow//tensorflow:windows": "%s.dll" % (name),
                "@org_tensorflow//tensorflow:macos": "lib%s%s.dylib" % (name, longsuffix),
                "//conditions:default": "lib%s.so%s" % (name, longsuffix),
            }),
            hdrs = hdrs,
            visibility = visibility,
        )

    native.filegroup(
        name = name + "_virtual",
        srcs = select({
            "@org_tensorflow//tensorflow:macos": [":lib%s%s.dylib" % (name, longsuffix)],
            "@org_tensorflow//tensorflow:ios": [":lib%s.dylib" % (name)],
            "@org_tensorflow//tensorflow:windows": [":%s.dll" % (name)],
            "//conditions:default": [":lib%s.so%s" % (name, longsuffix)],
        })
    )
