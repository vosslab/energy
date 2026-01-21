import pytest

from energylib import commonlib


#============================================
@pytest.mark.parametrize(
	"seconds, expected",
	[
		(0.1, "1.0e-01s"),
		(5.4, "5.4s"),
		(65, "01m:05s"),
		(3661, "01h:01m"),
		(90000, "01d:01h"),
	],
)
def test_humantime_formats(seconds, expected):
	cl = commonlib.CommonLib()
	assert cl.humantime(seconds) == expected


#============================================
@pytest.mark.parametrize(
	"value, expected",
	[
		("123", True),
		("001", True),
		("12a", False),
		("", False),
	],
)
def test_isint(value, expected):
	cl = commonlib.CommonLib()
	assert cl.isint(value) is expected


#============================================
def test_levenshtein_distance():
	cl = commonlib.CommonLib()
	assert cl.levenshtein("kitten", "sitting") == 3


#============================================
def test_compare_strings_ratio():
	cl = commonlib.CommonLib()
	assert cl.compareStrings("kitten", "sitting") == pytest.approx(3 / 7, rel=1e-9)
