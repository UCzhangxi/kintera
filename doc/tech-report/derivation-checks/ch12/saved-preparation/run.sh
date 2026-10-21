#!/bin/bash
set -eu
cd /home/tianhaol/fridica-snapy/worker2/ch12-cpu-cuda
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 CUDA_VISIBLE_DEVICES=0
export PYTHONPATH=/home/tianhaol/fridica-snapy/worker2/kintera-techreport-20261018/pyinst-cuda
export KINTERA_REPO=/home/tianhaol/fridica-snapy/worker2/kintera-techreport-20261018/kintera
export TMPDIR=$PWD/tmp CUDA_CACHE_PATH=$PWD/cache TORCHINDUCTOR_CACHE_DIR=$PWD/cache/torch
export PYTORCH_KERNEL_CACHE_PATH=$PWD/cache/torch-kernels
mkdir -p "$PYTORCH_KERNEL_CACHE_PATH"
mkdir -p "$TMPDIR" "$CUDA_CACHE_PATH"
exec /home/tianhaol/fridica-snapy/worker1/snapy-kintera130/.venv-kintera130-py311/bin/python "$@"
