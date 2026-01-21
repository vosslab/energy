import re
import sys
import types

import energylib

_fake_ecobee = types.SimpleNamespace()
energylib.ecobeelib = _fake_ecobee
sys.modules["energylib.ecobeelib"] = _fake_ecobee

from energylib import htmltools


#============================================
def test_number_to_html_color_clamps():
	color_low = htmltools.numberToHtmlColor(-1)
	color_zero = htmltools.numberToHtmlColor(0)
	color_high = htmltools.numberToHtmlColor(2)
	color_one = htmltools.numberToHtmlColor(1)
	assert color_low == color_zero
	assert color_high == color_one


#============================================
def test_color_price_formatting():
	result = htmltools.colorPrice(5.25, precision=1)
	assert "5.2&cent;" in result
	assert result.startswith("<span style='color: ")


#============================================
def test_color_temperature_formatting():
	result = htmltools.colorTemperature(72.3, precision=1)
	assert "72.3" in result
	assert "&deg;" in result


#============================================
def test_number_to_html_color_rgb_bounds():
	result = htmltools.numberToHtmlColor(0.5)
	match = re.match(r"rgb\((\d+), (\d+), (\d+)\)", result)
	assert match is not None
	for value in match.groups():
		channel = int(value)
		assert 0 <= channel <= 255


#============================================
def test_equivalent_gas_cost():
	assert htmltools.equivalent_gas_cost(10.0) == 1.4
