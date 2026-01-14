#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "${REPO_ROOT}"

/opt/homebrew/opt/python@3.12/bin/python3.12 "${REPO_ROOT}/tests/run_ascii_compliance.py"
