#!/bin/bash
# Deploy dashboard static files to the web root.
# Does not restart anything -- only copies static files.

set -e

REPO_ROOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
WEB_ROOT="/var/www/html"

echo "Deploying dashboard from $REPO_ROOT to $WEB_ROOT ..."

# Copy static files (flat layout, no subdirectories)
cp "$REPO_ROOT/html/dashboard.html" "$WEB_ROOT/dashboard.html"
cp "$REPO_ROOT/html/build/dashboard.js" "$WEB_ROOT/dashboard.js"

echo "Deployed:"
echo "  $WEB_ROOT/dashboard.html"
echo "  $WEB_ROOT/dashboard.js"
echo "Done. JSON data is written by generate_dashboard_data.py (tmux session)."
