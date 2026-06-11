"""
Tests for the stale-ComEd-price freshness gate introduced in M1-M3.

Coverage:
- Age primitive: getAgeOfLastPriceSeconds order-independence and ms->s conversion
- Predicate: isPriceDataFresh at several ages and edge cases
- awtrix3 gate (authoritative regression): prior-hour orange bar and stale text
- CLI helper: formatCliStatusLines returns ??? when stale
- Control consumers: wemo choose_action and thermostat get_comed_rates when stale
- Import smoke: successful import of comed_price_display confirms awtrix3 module loads

All fixtures use a fixed now_seconds derived from a concrete local date so tests
are deterministic and independent of the real clock.
"""
import os
import sys
import time
import types
import datetime
import importlib.util

import pytest

# REPO_ROOT is inserted into sys.path by tests/conftest.py; energylib is importable.
from energylib import comedlib

# awtrix3/comed_price_display.py self-inserts its REPO_ROOT into sys.path, but
# the module itself is not a package: add awtrix3/ so pytest can import it.
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
AWTRIX3_DIR = os.path.join(REPO_ROOT, "awtrix3")
if AWTRIX3_DIR not in sys.path:
	sys.path.insert(0, AWTRIX3_DIR)

# Guard awtrix3-dependent imports so missing optional deps skip rather than fail collection.
pytest.importorskip("yaml")
pytest.importorskip("numpy")
pytest.importorskip("requests")
import comed_price_display  # awtrix3 import smoke test: collection succeeds if this works

APPS_DIR = os.path.join(REPO_ROOT, "apps")


#============================================
# Shared fixture helpers
#============================================

def _load_wemo_module():
	"""Load apps/wemoPlug-comed-multi.py as a module object."""
	spec = importlib.util.spec_from_file_location(
		"wemo_multi",
		os.path.join(APPS_DIR, "wemoPlug-comed-multi.py"),
	)
	mod = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(mod)
	return mod


def _load_thermostat_module():
	"""
	Load apps/thermostat-comed.py with ecobeelib stubbed out.

	thermostat-comed.py does 'from energylib import ecobeelib' at import time.
	pyecobee is not installed in the test environment, so we inject a minimal
	stub before loading the module.
	"""
	fake_ecobeelib = types.ModuleType("energylib.ecobeelib")
	class _FakeMyEcobee:
		pass
	fake_ecobeelib.MyEcobee = _FakeMyEcobee
	# Inject under the exact key the module will look up
	sys.modules["energylib.ecobeelib"] = fake_ecobeelib

	spec = importlib.util.spec_from_file_location(
		"thermostat_comed",
		os.path.join(APPS_DIR, "thermostat-comed.py"),
	)
	mod = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(mod)
	return mod


def _make_comlib():
	"""Return a ComedLib instance with the persistent cache disabled."""
	comlib = comedlib.ComedLib()
	comlib.useCache = False
	# Prevent any accidental network call by clearing in-memory caches
	comlib.raw_data_cache = None
	comlib.parsed_data_cache = None
	return comlib


# Fixed reference time: 2026-06-10 21:03:00 local
# Using mktime with DST=-1 lets the OS resolve DST for this location and date.
_NOW_STRUCT = time.struct_time((2026, 6, 10, 21, 3, 0, 0, 0, -1))
NOW_SECONDS = time.mktime(_NOW_STRUCT)

# Convenience: seconds epoch for a sample N minutes before NOW_SECONDS
def _ms_before_now(minutes: int) -> str:
	"""Return millisUTC string for a sample that is `minutes` minutes before NOW_SECONDS."""
	sample_epoch = NOW_SECONDS - minutes * 60
	return str(int(sample_epoch * 1000))


def _stale_data():
	"""ComEd data with newest sample 7 hours (420 minutes) before NOW_SECONDS."""
	return [
		{"millisUTC": _ms_before_now(420), "price": "5.1"},
		{"millisUTC": _ms_before_now(425), "price": "4.9"},
	]


def _fresh_data():
	"""ComEd data with newest sample 5 minutes before NOW_SECONDS."""
	return [
		{"millisUTC": _ms_before_now(5), "price": "5.2"},
		{"millisUTC": _ms_before_now(8), "price": "4.9"},
	]


def _prior_hour_data():
	"""
	Data fixture for the authoritative awtrix3 prior-hour regression.

	now_seconds = 2026-06-10 21:03 local (hour 21).
	Newest sample = 20:58 local (hour 20), age = 5 minutes.
	The sample is fresh but from the prior clock hour, so compile_comed_price_data
	should return an orange progress bar (progressC == [255, 165, 0]).

	Include three samples all inside the 20:xx hour so parseComedData / rate
	getters can build a realistic bucket.
	"""
	# 20:58 = 5 min before 21:03
	# 20:55 = 8 min before
	# 20:52 = 11 min before
	return [
		{"millisUTC": _ms_before_now(5), "price": "5.2"},
		{"millisUTC": _ms_before_now(8), "price": "4.9"},
		{"millisUTC": _ms_before_now(11), "price": "5.1"},
	]


#============================================
# Age primitive tests
#============================================

def test_age_picks_newest_regardless_of_order():
	"""
	getAgeOfLastPriceSeconds returns the age of the newest sample no matter
	what order the items appear in the list.
	"""
	comlib = _make_comlib()
	# Two samples: 5 min ago (newest) and 7 hours ago (older)
	newest_ms = _ms_before_now(5)
	older_ms = _ms_before_now(420)
	data_asc = [
		{"millisUTC": older_ms, "price": "4.1"},
		{"millisUTC": newest_ms, "price": "5.2"},
	]
	data_desc = [
		{"millisUTC": newest_ms, "price": "5.2"},
		{"millisUTC": older_ms, "price": "4.1"},
	]
	age_asc = comlib.getAgeOfLastPriceSeconds(data_asc, NOW_SECONDS)
	age_desc = comlib.getAgeOfLastPriceSeconds(data_desc, NOW_SECONDS)
	# Both orderings must yield the same age (the newest = 5 min = ~300 seconds)
	assert abs(age_asc - age_desc) < 1


def test_age_milliseconds_to_seconds_conversion():
	"""
	A sample exactly 300 seconds before NOW_SECONDS has age ~300, not 300_000
	(if kept in ms) or 0.3 (if divided twice).
	"""
	comlib = _make_comlib()
	sample_seconds = NOW_SECONDS - 300
	data = [{"millisUTC": str(int(sample_seconds * 1000)), "price": "5.0"}]
	age = comlib.getAgeOfLastPriceSeconds(data, NOW_SECONDS)
	assert age is not None
	# age should be close to 300 seconds, not 300_000 (ms) or 0.3 (us)
	assert abs(age - 300) < 2


def test_age_missing_millisutc_returns_stale():
	"""
	isPriceDataFresh returns False when every item lacks a millisUTC key.

	The undeterminable age is treated as stale (strict-False policy).
	We do not assert the age value itself because the library may substitute 0.
	"""
	comlib = _make_comlib()
	no_ms_data = [{"price": "5.0"}, {"price": "4.5"}]
	# The predicate must be False; do not assert a specific age value
	assert comlib.isPriceDataFresh(no_ms_data, NOW_SECONDS) is False


#============================================
# Predicate tests
#============================================

def test_is_fresh_false_for_empty_data():
	"""isPriceDataFresh returns False for an empty list."""
	comlib = _make_comlib()
	assert comlib.isPriceDataFresh([], NOW_SECONDS) is False


def test_is_fresh_false_at_7_hours_old():
	"""isPriceDataFresh returns False when the newest sample is 7 hours old."""
	comlib = _make_comlib()
	assert comlib.isPriceDataFresh(_stale_data(), NOW_SECONDS) is False


def test_is_fresh_true_at_5_minutes_old():
	"""isPriceDataFresh returns True when the newest sample is 5 minutes old."""
	comlib = _make_comlib()
	assert comlib.isPriceDataFresh(_fresh_data(), NOW_SECONDS) is True


#============================================
# awtrix3 gate tests (authoritative regression)
#============================================

def test_awtrix3_prior_hour_shows_price_and_orange_bar():
	"""
	When the newest sample is fresh (5 min old) but in the previous clock hour,
	compile_comed_price_data returns a formatted price (not '???') and an orange
	progress bar (progressC == [255, 165, 0]).

	This is the authoritative regression for the age-first gate in awtrix3.
	"""
	data = _prior_hour_data()
	result = comed_price_display.compile_comed_price_data(data, NOW_SECONDS)
	# Must show a real price, not the stale placeholder
	assert result["text"] != "???"
	# Orange bar signals "fresh sample from the prior clock hour"
	assert result["progressC"] == [255, 165, 0]


def test_awtrix3_stale_data_shows_question_marks():
	"""
	When the newest sample is 7 hours old, compile_comed_price_data returns
	text == '???' regardless of the clock hour.
	"""
	result = comed_price_display.compile_comed_price_data(_stale_data(), NOW_SECONDS)
	assert result["text"] == "???"


#============================================
# CLI helper tests
#============================================

def test_cli_status_lines_contain_question_marks_when_stale():
	"""
	ComedLib.formatCliStatusLines returns lines containing '???' when the data
	is stale, so the operator is not shown a frozen price.
	"""
	comlib = _make_comlib()
	lines = comlib.formatCliStatusLines(_stale_data(), NOW_SECONDS)
	combined = "\n".join(lines)
	assert "???" in combined


#============================================
# Control consumer tests
#============================================

def test_wemo_choose_action_disables_when_stale():
	"""
	wemoPlug-comed-multi.choose_action returns action == 'disable' when the
	ComEd price data is stale (fail-safe off).
	"""
	pytest.importorskip("pywemo")
	comlib = _make_comlib()
	wemo = _load_wemo_module()
	now_dt = datetime.datetime(2026, 6, 10, 21, 3, 0)
	action, _msg = wemo.choose_action(comlib, _stale_data(), NOW_SECONDS, now_dt)
	assert action == "disable"


def test_thermostat_get_comed_rates_returns_fallback_when_stale():
	"""
	thermostat-comed.get_comed_rates returns (8.5, 8.5, 8.5) when the price
	data is stale, activating the conservative high-price path.
	"""
	comlib = _make_comlib()
	therm = _load_thermostat_module()
	current, predict, recent = therm.get_comed_rates(comlib, _stale_data(), NOW_SECONDS)
	assert current == therm.STALE_FALLBACK_PRICE_CENTS
	assert predict == therm.STALE_FALLBACK_PRICE_CENTS
	assert recent == therm.STALE_FALLBACK_PRICE_CENTS
