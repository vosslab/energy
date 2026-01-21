import pytest


pytest.skip(
	"WeMo control script requires networked hardware; skip unit tests.",
	allow_module_level=True,
)
