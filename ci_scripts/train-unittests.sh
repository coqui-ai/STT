#!/bin/bash
set -xe

source $(dirname "$0")/all-vars.sh
source $(dirname "$0")/all-utils.sh

set -o pipefail
apt install libopusfile0
pip install --upgrade pip setuptools wheel | cat
pip install --upgrade . | cat
set +o pipefail

python -m unittest
