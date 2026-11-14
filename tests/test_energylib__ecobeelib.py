# Standard Library
import os
import pickle
import pathlib
import datetime

# PIP3 modules
import pytz
import pytest

pytest.importorskip("pyecobee")

# Local repo modules
from energylib import ecobeelib


#============================================
@pytest.mark.parametrize("scope_name", ["SMART_READ", "SMART_WRITE", "EMS"])
def test_saved_credentials_preserve_tokens_and_expiry(
	tmp_path: pathlib.Path, scope_name: str,
) -> None:
	thermostat = ecobeelib.MyEcobee()
	thermostat.db_file = str(tmp_path / "credentials.pickle")
	thermostat.thermostat_name = "Test thermostat"
	thermostat.api_key = "a" * 32
	expires = datetime.datetime(2030, 1, 2, tzinfo=pytz.utc)
	scope = getattr(ecobeelib.pyecobee.Scope, scope_name)
	thermostat.ecobee_service = ecobeelib.pyecobee.EcobeeService(
		thermostat.thermostat_name, thermostat.api_key,
		authorization_token="test-authorization", access_token="test-access",
		refresh_token="test-refresh", access_token_expires_on=expires,
		refresh_token_expires_on=expires, scope=scope,
	)
	thermostat._persist_data()
	thermostat._load_data()
	service = thermostat.ecobee_service
	assert (service.authorization_token, service.access_token, service.refresh_token) == (
		"test-authorization", "test-access", "test-refresh",
	)
	assert (service.access_token_expires_on, service.refresh_token_expires_on, service.scope) == (
		expires, expires, scope,
	)


#============================================
def test_saved_credentials_reject_arbitrary_globals(tmp_path: pathlib.Path) -> None:
	thermostat = ecobeelib.MyEcobee()
	path = tmp_path / "credentials.pickle"
	path.write_bytes(pickle.dumps(os.system))
	thermostat.db_file = str(path)
	with pytest.raises(pickle.UnpicklingError, match="Unsupported credential type"):
		thermostat._load_data()


#============================================
class _UnsafeAttributeLookup:
	def __reduce__(self) -> tuple:
		return getattr, (ecobeelib.pyecobee.Scope, "__class__")


#============================================
def test_saved_credentials_reject_general_getattr(tmp_path: pathlib.Path) -> None:
	thermostat = ecobeelib.MyEcobee()
	path = tmp_path / "credentials.pickle"
	path.write_bytes(pickle.dumps(_UnsafeAttributeLookup()))
	thermostat.db_file = str(path)
	with pytest.raises(pickle.UnpicklingError, match="Unsupported Ecobee scope member"):
		thermostat._load_data()
