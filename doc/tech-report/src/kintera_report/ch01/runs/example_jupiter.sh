#!/bin/bash
# Chapter 1 (@sec-ch01): runs the repository's examples/example_jupiter.py from the checkout root and from examples/,
# to show that its relative card path only resolves in examples/. Its composition is random, so only the exit
# status and the error text are meant to be compared.
# Usage: KINTERA_REPO=<kintera checkout at the pin> bash example_jupiter.sh  (with kintera installed)
export CUDA_VISIBLE_DEVICES=""
cd "${KINTERA_REPO:?set KINTERA_REPO}"
echo "## from the checkout root"; python examples/example_jupiter.py 2>&1 | tail -1; echo "exit ${PIPESTATUS[0]}"
cd examples
echo "## from examples/"; python example_jupiter.py > /dev/null 2>&1; echo "exit $?"
