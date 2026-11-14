import importlib.util
import os
import unittest.mock

import pytest
import file_utils


#============================================
@pytest.fixture
def wemo(monkeypatch):
	"""Load the controller with hardware calls mocked."""
	pytest.importorskip("pywemo")
	path = os.path.join(file_utils.get_repo_root(), "apps", "wemoPlug-comed-multi.py")
	spec = importlib.util.spec_from_file_location("wemo_multi", path)
	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)
	monkeypatch.setattr(module.time, "sleep", unittest.mock.Mock())
	return module


#============================================
@pytest.mark.parametrize("action", ["enable", "disable"])
def test_missing_description_url_skips_device_fetch(wemo, monkeypatch, action):
	monkeypatch.setattr(wemo.pywemo, "setup_url_for_address", unittest.mock.Mock(return_value=None))
	fetch = unittest.mock.Mock()
	monkeypatch.setattr(wemo.pywemo.discovery, "device_from_description", fetch)
	plug = wemo.ComedSmartWemoPlug("192.0.2.1", debug_wemo=True)
	getattr(plug, action)()
	fetch.assert_not_called()
	assert not plug.connected


#============================================
def test_failed_description_recovers_on_next_action(wemo, monkeypatch):
	monkeypatch.setattr(wemo.pywemo, "setup_url_for_address", unittest.mock.Mock(
		return_value="http://192.0.2.1:49153/setup.xml"))
	device = unittest.mock.Mock()
	device.get_state.return_value = 1
	monkeypatch.setattr(wemo.pywemo.discovery, "device_from_description", unittest.mock.Mock(
		side_effect=[None, device]))
	plug = wemo.ComedSmartWemoPlug("192.0.2.1", debug_wemo=True)
	plug.enable()
	assert plug.connected
	device.get_state.assert_called_with(force_update=True)


#============================================
def test_unavailable_plug_does_not_block_other_plugs(wemo, monkeypatch):
	monkeypatch.setattr(wemo.pywemo, "setup_url_for_address", unittest.mock.Mock(return_value=None))
	unavailable = wemo.ComedSmartWemoPlug("192.0.2.1")
	healthy = unittest.mock.Mock(address="192.0.2.2")
	wemo._apply_action([unavailable, healthy], "disable", "disable charging")
	healthy.disable.assert_called_once_with()
