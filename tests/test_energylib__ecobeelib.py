import pytest


pytest.skip(
	"ecobeelib requires filesystem state and network access; skip unit tests.",
	allow_module_level=True,
)
