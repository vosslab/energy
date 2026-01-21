import energylib


#============================================
def test_module_docstring():
	assert "energy" in (energylib.__doc__ or "").lower()
