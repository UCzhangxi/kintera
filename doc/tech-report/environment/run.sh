#!/usr/bin/env bash
set -euo pipefail
# Trust only the user-supplied bind-mounted checkout inside this disposable container.
git config --global --add safe.directory /work
cd /work/doc/tech-report
mkdir -p .reproduce/{cache,texmf-var,texmf-config,tmp,logs}
trap 'chown -R "${OUTPUT_UID:-0}:${OUTPUT_GID:-0}" .reproduce build book/_book book/_freeze 2>/dev/null || true' EXIT
export XDG_CACHE_HOME="$PWD/.reproduce/cache"
export TEXMFVAR="$PWD/.reproduce/texmf-var" TEXMFCONFIG="$PWD/.reproduce/texmf-config"
export TMPDIR="$PWD/.reproduce/tmp" MPLCONFIGDIR="$PWD/.reproduce/cache/matplotlib"
export KINTERA_REPO="$PWD/.reproduce/sources/kintera" KINTERA_WT="$PWD/.reproduce/sources/kintera"
export CH12_SAVED="$PWD/derivation-checks/ch12/saved-preparation"
export KINTERA_REPORT_CACHE="$PWD/.reproduce/cache/anchors" CHECK_CITATIONS_CACHE="$PWD/.reproduce/cache/citations"
export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 MAX_JOBS=2 MPLBACKEND=Agg
cp /opt/system-packages.lock .reproduce/logs/system-packages.lock
python -m pip list --format=freeze > .reproduce/logs/python-packages-before.lock
python environment/build_sources.py 2>&1 | tee .reproduce/logs/build.log
python -m pip list --format=freeze > .reproduce/logs/python-packages-after.lock
python environment/smoke.py 2>&1 | tee .reproduce/logs/smoke.log
if [[ ${1:-audit} == audit ]]; then
    python environment/audit.py
fi
