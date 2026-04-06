#!/bin/bash
# Deploy dashboard static files to the web root.
# Does not restart anything -- only copies static files.

set -e

REPO_ROOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
WEB_ROOT="/var/www/html"

echo "Deploying dashboard from $REPO_ROOT to $WEB_ROOT ..."

# Create api directory if needed
mkdir -p "$WEB_ROOT/api"
mkdir -p "$WEB_ROOT/build"

# Copy static files
cp "$REPO_ROOT/html/dashboard.html" "$WEB_ROOT/dashboard.html"
cp "$REPO_ROOT/html/build/dashboard.js" "$WEB_ROOT/build/dashboard.js"

echo "Deployed:"
echo "  $WEB_ROOT/dashboard.html"
echo "  $WEB_ROOT/build/dashboard.js"
echo "Done. JSON data is written by generate_dashboard_data.py (tmux session)."
