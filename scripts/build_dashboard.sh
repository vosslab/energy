#!/bin/bash
# Build dashboard TypeScript on any system.
# Installs Node.js and TypeScript if needed.

set -e

REPO_ROOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
HTML_DIR="$REPO_ROOT/html"

# Check for node
if ! command -v node >/dev/null 2>&1; then
  echo "Node.js not found. Install it:"
  echo "  Debian/Ubuntu: sudo apt install nodejs npm"
  echo "  macOS:         brew install node"
  exit 1
fi

# Check for npx
if ! command -v npx >/dev/null 2>&1; then
  echo "npx not found. Install npm:"
  echo "  Debian/Ubuntu: sudo apt install npm"
  echo "  macOS:         brew install node"
  exit 1
fi

# Install TypeScript locally if not present
if [ ! -d "$HTML_DIR/node_modules/typescript" ]; then
  echo "Installing TypeScript locally..."
  cd "$HTML_DIR" && npm install typescript
fi

# Compile
echo "Compiling TypeScript..."
cd "$HTML_DIR" && npx tsc

echo "Built: $HTML_DIR/build/dashboard.js"
