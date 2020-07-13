#!/usr/bin/env python3

import sys
import logging
import shelve
from datetime import datetime

import pytz
from six.moves import input

logger = logging.getLogger(__name__)
out_hdlr = logging.StreamHandler(sys.stdout)
out_hdlr.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
out_hdlr.setLevel(logging.INFO)
logger.addHandler(out_hdlr)
logger.setLevel(logging.DEBUG)

from pyecobee import *

def persist_to_shelf(file_name, ecobee_service):
    pyecobee_db = shelve.open(file_name, protocol=2)
    pyecobee_db[ecobee_service.thermostat_name] = ecobee_service
    pyecobee_db.close()


def refresh_tokens(ecobee_service):
    token_response = ecobee_service.refresh_tokens()
    logger.debug('TokenResponse returned from ecobee_service.refresh_tokens():\n{0}'.format(
        token_response.pretty_format()))

    persist_to_shelf('pyecobee_db', ecobee_service)


def request_tokens(ecobee_service):
    token_response = ecobee_service.request_tokens()
    logger.debug('TokenResponse returned from ecobee_service.request_tokens():\n{0}'.format(
        token_response.pretty_format()))

    persist_to_shelf('pyecobee_db', ecobee_service)


def authorize(ecobee_service):
    authorize_response = ecobee_service.authorize()
    logger.debug('AutorizeResponse returned from ecobee_service.authorize():\n{0}'.format(
        authorize_response.pretty_format()))

    persist_to_shelf('pyecobee_db', ecobee_service)

    logger.info('Please goto ecobee.com, login to the web portal and click on the settings tab. Ensure the My '
                'Apps widget is enabled. If it is not click on the My Apps option in the menu on the left. In the '
                'My Apps widget paste "{0}" and in the textbox labelled "Enter your 4 digit pin to '
                'install your third party app" and then click "Install App". The next screen will display any '
                'permissions the app requires and will ask you to click "Authorize" to add the application.\n\n'
                'After completing this step please hit "Enter" to continue.'.format(
        authorize_response.ecobee_pin))
    input()

def open():
    thermostat_name = 'Voss Ecobee'
    try:
        pyecobee_db = shelve.open('pyecobee_db', protocol=2)
        ecobee_service = pyecobee_db[thermostat_name]
    except KeyError:
        application_key = input('Please enter the API key of your ecobee App: ')
        ecobee_service = EcobeeService(thermostat_name=thermostat_name, application_key=application_key)
    finally:
        pyecobee_db.close()

    if not ecobee_service.authorization_token:
        authorize(ecobee_service)

    if not ecobee_service.access_token:
        request_tokens(ecobee_service)

    now_utc = datetime.now(pytz.utc)
    if now_utc > ecobee_service.refresh_token_expires_on:
        authorize(ecobee_service)
        request_tokens(ecobee_service)
    elif now_utc > ecobee_service.access_token_expires_on:
        token_response = ecobee_service.refresh_tokens()

    # Now make your requests :)

    thermostat_summary_response = ecobee_service.request_thermostats_summary(selection=Selection(
        selection_type=SelectionType.REGISTERED.value,
        selection_match='311019859090',
        include_equipment_status=True))
    logger.info(thermostat_summary_response.pretty_format())

    # Only set the include options you need to True. I've set most of them to True for illustrative purposes only.
    selection = Selection(selection_type=SelectionType.REGISTERED.value, selection_match='311019859090', 
                      include_alerts=False,
                      include_device=False, include_electricity=False, include_equipment_status=True,
                      include_events=False, include_extended_runtime=False, include_house_details=False,
                      include_location=False, include_management=False, include_notification_settings=False,
                      include_oem_cfg=False, include_privacy=False, include_program=False, include_reminders=False,
                      include_runtime=True, include_security_settings=False, include_sensors=True,
                      include_settings=True, include_technician=False, include_utility=False, include_version=False,
                      include_weather=False)
    thermostat_response = ecobee_service.request_thermostats(selection)
    logger.info(thermostat_response.pretty_format())
    assert thermostat_response.status.code == 0, 'Failure while executing request_thermostats:\n{0}'.format(
        thermostat_response.pretty_format())

    print(dir(thermostat_response))
    thermostat_obj = thermostat_response.thermostat_list[0]
    print(dir(thermostat_obj))
    for sensor in thermostat_obj.remote_sensors:
        temp = float(sensor.capability[0].value)/10.
        print("{0}  {1}".format(temp, sensor.name))


    # Specifically the cooling temperature to use and hold indefinitely
    #update_thermostat_response = ecobee_service.set_hold(cool_hold_temp=79, heat_hold_temp=58, hold_type=HoldType.INDEFINITE)
    #logger.info(update_thermostat_response.pretty_format())
    #assert update_thermostat_response.status.code == 0, 'Failure while executing set_hold:\n{0}'.format(
    #    update_thermostat_response.pretty_format())

    #update_thermostat_response = ecobee_service.set_hold(hold_climate_ref='away', hold_type=HoldType.NEXT_TRANSITION)
    #logger.info(update_thermostat_response.pretty_format())
    #assert update_thermostat_response.status.code == 0, 'Failure while executing set_hold:\n{0}'.format(
    #    update_thermostat_response.pretty_format()

if __name__ == '__main__':
    open()
