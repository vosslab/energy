import pytest


pytest.skip(
	"Thermostat control script needs external services and time-based IO; skip unit tests.",
	allow_module_level=True,
)
