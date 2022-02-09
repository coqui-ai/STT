#! /usr/bin/env python

import os
import subprocess
import sys
from distutils.command.build import build

from setuptools import Extension, setup


def main():
    try:
        import numpy

        try:
            numpy_include = numpy.get_include()
        except AttributeError:
            numpy_include = numpy.get_numpy_include()
    except ImportError:
        numpy_include = ""
        assert "NUMPY_INCLUDE" in os.environ

    def read(fname):
        return open(os.path.join(os.path.dirname(__file__), fname)).read()

    numpy_include = os.getenv("NUMPY_INCLUDE", numpy_include)
    numpy_min_ver = os.getenv("NUMPY_DEP_VERSION", "")

    project_name = "STT"
    if "--project_name" in sys.argv:
        project_name_idx = sys.argv.index("--project_name")
        project_name = sys.argv[project_name_idx + 1]
        sys.argv.remove("--project_name")
        sys.argv.pop(project_name_idx)

    with open("../../training/coqui_stt_training/VERSION", "r") as ver:
        project_version = ver.read().strip()

    class BuildExtFirst(build):
        sub_commands = [
            ("build_ext", build.has_ext_modules),
            ("build_py", build.has_pure_modules),
            ("build_clib", build.has_c_libraries),
            ("build_scripts", build.has_scripts),
        ]

    # Properly pass arguments for linking, setuptools will perform some checks
    def lib_dirs_split(a):
        if os.name == "posix":
            return a.split("-L")[1:]

        if os.name == "nt":
            return []

        raise AssertionError("os.name == java not expected")

    def libs_split(a):
        if os.name == "posix":
            return a.split("-l")[1:]

        if os.name == "nt":
            return a.split(".lib")[0:1]

        raise AssertionError("os.name == java not expected")

    ds_ext = Extension(
        name="stt._impl",
        sources=["impl.i"],
        include_dirs=[numpy_include, "../"],
        library_dirs=list(
            map(lambda x: x.strip(), lib_dirs_split(os.getenv("MODEL_LDFLAGS", "")))
        ),
        libraries=list(
            map(lambda x: x.strip(), libs_split(os.getenv("MODEL_LIBS", "")))
        ),
        swig_opts=["-c++", "-keyword"],
    )

    setup(
        name=project_name,
        description="A library for doing speech recognition using a Coqui STT model",
        long_description=read("README.rst"),
        long_description_content_type="text/x-rst; charset=UTF-8",
        author="Coqui GmbH",
        version=project_version,
        package_dir={"stt": "."},
        cmdclass={"build": BuildExtFirst},
        license="MPL-2.0",
        url="https://github.com/coqui-ai/STT",
        project_urls={
            "Documentation": "https://stt.readthedocs.io",
            "Tracker": "https://github.com/coqui-ai/STT/issues",
            "Repository": "https://github.com/coqui-ai/STT/tree/v{}".format(
                project_version
            ),
            "Discussions": "https://github.com/coqui-ai/STT/discussions",
        },
        ext_modules=[ds_ext],
        py_modules=["stt", "stt.client", "stt.impl"],
        entry_points={"console_scripts": ["stt=stt.client:main"]},
        install_requires=["numpy%s" % numpy_min_ver],
        include_package_data=True,
        classifiers=[
            "Development Status :: 3 - Alpha",
            "Environment :: Console",
            "Intended Audience :: Developers",
            "Intended Audience :: Science/Research",
            "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
            "Programming Language :: Python :: 2.7",
            "Programming Language :: Python :: 3.4",
            "Programming Language :: Python :: 3.5",
            "Programming Language :: Python :: 3.6",
            "Topic :: Multimedia :: Sound/Audio :: Speech",
            "Topic :: Scientific/Engineering :: Human Machine Interfaces",
            "Topic :: Scientific/Engineering",
            "Topic :: Utilities",
        ],
    )


if __name__ == "__main__":
    main()
