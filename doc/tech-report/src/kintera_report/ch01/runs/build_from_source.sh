#!/bin/bash
# Chapter 1 (@sec-ch01) quick start, source route: the README "Installation / Quick Start" steps of kintera at
# kintera@0d9f67f97d841147e23283d2dcdab302238d2c45, run in a fresh virtual environment, CPU only.
#
# Usage: KINTERA_REPO=<kintera checkout at the pin> bash build_from_source.sh <new venv directory>
# Needs a C++17 compiler (the README asks for GCC 9 or later), CMake 3.18 or later and the NetCDF C library.
# Recorded output: src/kintera_report/ch01/data/build_from_source.out
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
LOCK="$HERE/../../../../environment/python.lock"
export CUDA_VISIBLE_DEVICES=""
VENV=${1:?give a directory for the new virtual environment}
python3 -m venv "$VENV"
"$VENV/bin/pip" install -q -r "$LOCK"
# README step 1. pyharp's wheels link against the CUDA build of torch, so torch comes from PyPI as written.
"$VENV/bin/pip" install -q numpy 'torch==2.10.0' 'pyharp==2.7.6'
export PATH="$VENV/bin:$PATH"
cd "${KINTERA_REPO:?set KINTERA_REPO}"
git rev-parse HEAD
gcc --version | head -1; cmake --version | head -1; python --version
# README step 3
cmake -B build -DCMAKE_BUILD_TYPE=Release -DCUDA=OFF
cmake --build build --parallel "${MAX_JOBS:-2}"
# README step 4
pip install --no-build-isolation --no-deps .
pip list 2>/dev/null | grep -iE '^(kintera|torch|pyharp|pydisort|numpy) '
python -c "import kintera; print('kintera', kintera.__version__)"
