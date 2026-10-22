#!/usr/bin/env bash
# Run from any directory; outputs and caches remain inside this checkout.
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
root=$(git -C "$here" rev-parse --show-toplevel)
export DOCKER_CONFIG="$root/doc/tech-report/.reproduce/docker-config"
mkdir -p "$DOCKER_CONFIG"
docker build --platform linux/amd64 -t kintera-report-reproduce "$here"
# Container root can install source packages; chown only this run's outputs on exit.
docker run --rm --platform linux/amd64 -v "$root:/work" \
    -e OUTPUT_UID="$(id -u)" -e OUTPUT_GID="$(id -g)" \
    -e MAX_JOBS="${MAX_JOBS:-2}" \
    kintera-report-reproduce bash /work/doc/tech-report/environment/run.sh "${1:-audit}"
