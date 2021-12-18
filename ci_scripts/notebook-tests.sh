#!/bin/bash
set -xe

source $(dirname "$0")/all-vars.sh
source $(dirname "$0")/all-utils.sh

for python_notebook in ./notebooks/*.ipynb; do
    time jupyter nbconvert --to notebook --execute $python_notebook
done
