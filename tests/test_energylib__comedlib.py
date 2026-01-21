import numpy

from energylib import comedlib


#============================================
def _sample_data(prices):
	return [{"price": str(price)} for price in prices]


#============================================
def _new_comedlib(monkeypatch):
	monkeypatch.setattr(comedlib.os.path, "exists", lambda _: True)
	return comedlib.ComedLib()


#============================================
def test_get_median_comed_rate(monkeypatch):
	comlib = _new_comedlib(monkeypatch)
	prices = [1.0, 2.0, 3.0, 4.0]
	median, std = comlib.getMedianComedRate(_sample_data(prices))
	expected_median = numpy.percentile(numpy.array(prices, dtype=numpy.float64), 75)
	expected_std = numpy.std(numpy.array(prices, dtype=numpy.float64))
	assert median == expected_median
	assert std == expected_std


#============================================
def test_get_url(monkeypatch):
	comlib = _new_comedlib(monkeypatch)
	assert comlib.getUrl().startswith("https://")
