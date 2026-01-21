import pytest


pytest.skip(
	"Ecobee script requires external services and IO; skip unit tests.",
	allow_module_level=True,
)
