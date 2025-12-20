#!/usr/bin/env python3

import importlib

_mod = importlib.import_module("energylib.ecobeelib")


def __getattr__(name):
	return getattr(_mod, name)


def __dir__():
	return sorted(set(globals().keys()) | set(dir(_mod)))
