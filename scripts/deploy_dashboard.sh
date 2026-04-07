#!/bin/bash
# Deploy dashboard static files to the web root.
# Does not restart anything -- only copies static files.
#
# Build step: compile TypeScript locally before deploying.
# The server does not need TypeScript installed.

set -e

REPO_ROOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
WEB_ROOT="/var/www/html"
HTML_DIR="$REPO_ROOT/html"

# Build TypeScript if npx/tsc is available
if command -v npx >/dev/null 2>&1; then
  echo "Compiling TypeScript..."
  cd "$HTML_DIR" && npx tsc
  cd "$REPO_ROOT"
fi

# Check that compiled JS exists
if [ ! -f "$HTML_DIR/build/dashboard.js" ]; then
  echo "ERROR: $HTML_DIR/build/dashboard.js not found."
  echo "Compile TypeScript on your dev machine first: cd html && npx tsc"
  exit 1
fi

echo "Deploying dashboard from $REPO_ROOT to $WEB_ROOT ..."

# Copy static files (flat layout, no subdirectories)
cp "$HTML_DIR/dashboard.html" "$WEB_ROOT/dashboard.html"
cp "$HTML_DIR/build/dashboard.js" "$WEB_ROOT/dashboard.js"

echo "Deployed:"
echo "  $WEB_ROOT/dashboard.html"
echo "  $WEB_ROOT/dashboard.js"
echo "Done. JSON data is written by generate_dashboard_data.py (tmux session)."
