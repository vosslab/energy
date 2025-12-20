#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PY_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PY_ROOT}"

# Run pyflakes on all Python files and capture output
pyflakes $(find "${PY_ROOT}" -type f -name "*.py" -print) > pyflakes.txt 2>&1 || true

RESULT=$(wc -l < pyflakes.txt)

# Success if no errors were found
if [ "${RESULT}" -eq 0 ]; then
    echo "No errors found!!!"
    exit 0
fi

echo "First 5 errors"
head -n 5 pyflakes.txt
echo ""

echo "Last 5 errors"
tail -n 5 pyflakes.txt
echo ""

echo "Found ${RESULT} pyflakes errors"

# Fail if any errors were found
exit 1
