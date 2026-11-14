# source_me.sh - shell environment for running this repo's Python.
# Usage: source source_me.sh && python3 ...
# This is a bash script sourced into your shell, not run directly.

# Require bash: the checks below and the repo's tab-indented shell style are
# bash-specific. Fail loudly rather than misbehave under another shell.
set | grep -q '^BASH_VERSION=' || echo "use bash for your shell"
set | grep -q '^BASH_VERSION=' || exit 1

# Source ~/.bashrc FIRST, before any repo-specific environment extension below.
# ~/.bashrc applies local shell setup (PATH, etc.) and resets some variables --
# it clears PYTHONPATH (verified). Anything that sets PYTHONPATH must run after
# this line, or ~/.bashrc would wipe it.
source ~/.bashrc

# Python runtime defaults: unbuffered stdout/stderr, and no .pyc/__pycache__
# files written on import.
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1

# --- Optional: repo-root import path (disabled by default) -------------------
# Uncomment ONLY if this repo needs its repo-root modules importable when
# commands run from a subdirectory without installing the repo -- most commonly
# a repo-root package imported package-qualified (e.g. `import mypkg.thing`)
# from an application-facing launcher, or tests that import repo-root modules.
# Must come after sourcing ~/.bashrc, which clears PYTHONPATH.
# Assumes the repo is inside a Git work tree (git rev-parse).
#REPO_ROOT="$(git rev-parse --show-toplevel)"
#export PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}"
#unset REPO_ROOT
