#!/bin/bash
# Chapter 1 (@sec-ch01) quick start, PyPI route: a fresh virtual environment, `pip install kintera`, then the
# quick-start script. PyPI's kintera need not be the code pin; the version installed is printed.
#
# Usage: KINTERA_REPO=<kintera checkout at the pin, for examples/jupiter.yaml> bash pip_install.sh <new venv dir>
# Recorded output: src/kintera_report/ch01/data/pip_install.out
set -euo pipefail
export CUDA_VISIBLE_DEVICES=""
VENV=${1:?give a directory for the new virtual environment}
HERE=$(cd "$(dirname "$0")" && pwd)
python3 -m venv "$VENV"
"$VENV/bin/pip" install -q -r "$HERE/../../../../environment/python.lock"
"$VENV/bin/pip" install -q "pyharp==2.7.6" "kintera==2.6.4"
"$VENV/bin/pip" list 2>/dev/null | grep -iE '^(kintera|torch|pyharp|pydisort|numpy) '
"$VENV/bin/python" -P "$HERE/quick_start.py"
