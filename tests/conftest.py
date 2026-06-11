# Exclude both end-to-end tiers from pytest collection. tests/playwright/
# holds browser-driven tests (Playwright), and tests/e2e/ holds heavier
# shell/Python whole-system runners. Both run outside pytest -- see
# docs/PLAYWRIGHT_USAGE.md and docs/E2E_TESTS.md.
collect_ignore = ["e2e", "playwright"]

# Re-export the canonical skip-dirs set so callers can reference it here.
# The authoritative definition lives in git_file_utils.HYGIENE_SKIP_DIRS.
# Lint tests import git_file_utils directly and use that name.

import os
import sys

import pytest

import git_file_utils

# Canonical skip-dirs set: single source of truth lives in git_file_utils.
# Reference it here so callers that import conftest can also reach it.
HYGIENE_SKIP_DIRS = git_file_utils.HYGIENE_SKIP_DIRS

REPO_ROOT = git_file_utils.get_repo_root()
SKIP_ENV = "SKIP_REPO_HYGIENE"

if REPO_ROOT not in sys.path:
	sys.path.insert(0, REPO_ROOT)

TESTS_DIR = os.path.abspath(os.path.dirname(__file__))
if TESTS_DIR not in sys.path:
	sys.path.insert(0, TESTS_DIR)


#============================================
@pytest.fixture
def repo_root() -> str:
	"""
	Provide the repository root path.
	"""
	return REPO_ROOT


#============================================
def pytest_addoption(parser) -> None:
	"""
	Add repo hygiene options.
	"""
	group = parser.getgroup("repo-hygiene")
	group.addoption(
		"--no-ascii-fix",
		action="store_true",
		help="Disable auto-fix for ASCII compliance tests.",
	)


#============================================
@pytest.fixture
def skip_repo_hygiene() -> bool:
	"""
	Check whether repo hygiene tests should be skipped.
	"""
	return os.environ.get(SKIP_ENV) == "1"


#============================================
@pytest.fixture
def ascii_fix_enabled(request) -> bool:
	"""
	Check whether ASCII compliance auto-fix is enabled.
	"""
	return not request.config.getoption("--no-ascii-fix")
