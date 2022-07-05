import os
import platform
import sys
from pathlib import Path

from pkg_resources import parse_version
from setuptools import find_packages, setup


def main():
    version_file = Path(__file__).parent / "training" / "coqui_stt_training" / "VERSION"
    with open(str(version_file)) as fin:
        version = fin.read().strip()

    install_requires_base = [
        "attrdict",
        "bs4",
        "coqpit",
        "numpy",
        "optuna",
        "numba <= 0.53.1",
        "opuslib == 2.0.0",
        "pandas",
        "progressbar2",
        "protobuf <= 3.20.1",
        "pyogg >= 0.6.14a1",
        "resampy >= 0.2.2",
        "requests",
        "semver",
        "six",
        "sox",
        "soundfile",
        "tqdm",
        "webdataset==0.1.103",
        "miniaudio",
        "clearml",
    ]

    decoder_pypi_dep = ["coqui_stt_ctcdecoder == {}".format(version)]

    tensorflow_pypi_dep = ["tensorflow == 1.15.4"]

    if os.environ.get("DS_NODECODER", ""):
        install_requires = install_requires_base
    else:
        install_requires = install_requires_base + decoder_pypi_dep

    if os.environ.get("DS_NOTENSORFLOW", ""):
        install_requires = install_requires
    else:
        install_requires = install_requires + tensorflow_pypi_dep

    setup(
        name="coqui_stt_training",
        version=version,
        description="Training code for Coqui STT",
        url="https://github.com/coqui-ai/STT",
        author="Coqui STT authors",
        license="MPL-2.0",
        # Classifiers help users find your project by categorizing it.
        #
        # For a list of valid classifiers, see https://pypi.org/classifiers/
        classifiers=[
            "Development Status :: 3 - Alpha",
            "Intended Audience :: Developers",
            "Topic :: Multimedia :: Sound/Audio :: Speech",
            "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
            "Programming Language :: Python :: 3",
        ],
        package_dir={"": "training"},
        packages=find_packages(where="training"),
        python_requires=">=3.7, <3.9",
        install_requires=install_requires,
        include_package_data=True,
        extras_require={
            "transcribe": ["webrtcvad == 2.0.10"],
            "onnxruntime": ["onnxruntime==1.11.0"],
        },
    )


if __name__ == "__main__":
    main()
