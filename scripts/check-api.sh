#!/usr/bin/env sh
set -eu

cd "$(dirname "$0")/../apps/api"
"${PYTHON:-python3}" -m pytest
