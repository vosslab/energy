import pytest


pytest.skip(
	"solarProduction uses network and hardware dependencies; skip unit tests.",
	allow_module_level=True,
)
