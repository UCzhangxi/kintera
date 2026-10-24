#!/usr/bin/env bash
# Run inside the committed report environment. OUT must be a new writable directory.
set -eu
report=$(cd "$(dirname "$0")/.." && pwd)
out=$(realpath -m "${1:?usage: run_source_checks.sh NEW_OUTPUT_DIRECTORY}")
test ! -e "$out"
mkdir -p "$out"
git clone https://github.com/chengcli/kintera.git "$out/source"
cd "$out/source"
pre=53f3ffcc6fefd34513dc04214d506103b2d917ed
main=e357792d50639d68e9090b542edf038d2b029aa2
for variant in pre clean floor atoms energy; do
  pin=$main
  if [ "$variant" = pre ]; then pin=$pre; fi
  git checkout --detach "$pin"
  if [ "$variant" != pre ] && [ "$variant" != clean ]; then
    python "$report/invariants/mutate_sources.py" "$PWD" "$variant" > "$out/$variant.patch"
  fi
  git rev-parse HEAD > "$out/$variant.source"
  cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DCUDA=OFF -DNETCDF=ON > "$out/$variant-configure.log" 2>&1
  cmake --build build --parallel "${MAX_JOBS:-2}" > "$out/$variant-build.log" 2>&1
  MAX_JOBS="${MAX_JOBS:-2}" python -m pip install --no-build-isolation --no-deps --target "_pyinstall_$variant" . > "$out/$variant-install.log" 2>&1
  set +e
  PYTHONPATH="$PWD/_pyinstall_$variant" python "$report/invariants/check_invariants.py" --output "$out/$variant.json" > "$out/$variant-run.log" 2>&1
  code=$?
  set -e
  echo "$code" > "$out/$variant.exit"
  if [ "$variant" = clean ]; then test "$code" = 0; else test "$code" = 1; fi
  git restore -- src
 done
python "$report/invariants/verify_break_results.py" "$out"
