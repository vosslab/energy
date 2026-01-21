import pytest


pytest.skip(
	"CLI script performs network requests and file IO; skip unit tests.",
	allow_module_level=True,
)
