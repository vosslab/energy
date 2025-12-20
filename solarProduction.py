#!/usr/bin/env python3

import importlib

_mod = importlib.import_module("energylib.solarProduction")


def __getattr__(name):
	return getattr(_mod, name)


def __dir__():
	return sorted(set(globals().keys()) | set(dir(_mod)))


if __name__ == "__main__":
	import runpy

	runpy.run_module("energylib.solarProduction", run_name="__main__")
