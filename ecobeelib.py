#!/usr/bin/env python

import os
import sys
import pytz
import yaml
import numpy
import shelve
import logging
import pyecobee
import datetime
from six import moves

class MyEcobee(object):
	def __init__(self):
		self.setPyEcobeeDbFile()
		self.setYamlFile()

	def setPyEcobeeDbFile(self):
		if os.path.exists('/etc/energy/pyecobee_db.shelf'):
			self.shelf_file = '/etc/energy/pyecobee_db.shelf'
		elif os.path.exists('pyecobee_db.shelf'):
			self.shelf_file = 'pyecobee_db.shelf'
		elif os.path.exists('pyecobee_db'):
			self.shelf_file = 'pyecobee_db'
		#default value
		self.shelf_file = '/etc/energy/pyecobee_db.shelf'
		return

	def setYamlFile(self):
		if os.path.exists("/etc/energy/ecobee_defs.yml"):
			self.yaml_file = "/etc/energy/ecobee_defs.yml"
		elif os.path.exists("ecobee_defs.yml"):
			self.yaml_file = "ecobee_defs.yml"
		return

	def _persist_to_shelf(self):
		pyecobee_db = shelve.open(self.shelf_file, protocol=2)
		pyecobee_db[self.thermostat_name] = self.ecobee_service
		pyecobee_db.close()

	def _refresh_tokens(self):
		token_response = self.ecobee_service.refresh_tokens()
		self.logger.debug('TokenResponse returned from self.ecobee_service.refresh_tokens():\n{0}'.format(token_response.pretty_format()))
		self._persist_to_shelf()

	def _request_tokens(self):
		token_response = self.ecobee_service.request_tokens()
		self.logger.debug('TokenResponse returned from self.ecobee_service.request_tokens():\n{0}'.format(token_response.pretty_format()))
		self._persist_to_shelf()

	def _authorize(self):
		authorize_response = self.ecobee_service.authorize()
		self.logger.debug('AutorizeResponse returned from self.ecobee_service.authorize():\n{0}'.format(authorize_response.pretty_format()))
		self._persist_to_shelf()
		self.logger.info('Please goto ecobee.com, login to the web portal and click on the settings tab.\n'
			'Ensure the My Apps widget is enabled.\n'
			'If it is not click on the My Apps option in the menu on the left.\n'
			'In the My Apps widget paste "{0}" and in the textbox labelled'
			'"Enter your 4 digit pin to install your third party app" and then click "Install App". \n'
			'The next screen will display any permissions the app requires and will ask you to click\n'
			'"Authorize" to add the application.\n\n'
			'After completing this step please hit "Enter" to continue.'.format(authorize_response.ecobee_pin))
		moves.input()

	def _request_data(self, selection):
		thermostat_response = self.ecobee_service.request_thermostats(selection)
		self.logger.debug(thermostat_response.pretty_format())
		assert thermostat_response.status.code == 0, 'Failure while executing request_thermostats:\n{0}'.format(
			thermostat_response.pretty_format())
		return thermostat_response

	#================================================================
	#================================================================
	# SYSTEM FUNCTIONS TO CALL
	#================================================================
	#================================================================

	def readThermostatDefs(self):
		self.logger.debug('Reading txt file: {0}'.format(self.yaml_file))
		pyecobee_defs = open(self.yaml_file, 'r')
		fulldata = yaml.load(pyecobee_defs, yaml.SafeLoader)
		self.thermostat_name = fulldata['thermostat_name'].strip()
		self.api_key = fulldata['api_key'].strip()
		self.thermostat_id = str(fulldata['thermostat_id'])
		pyecobee_defs.close()

	def openConnection(self):
		try:
			pyecobee_db = shelve.open(self.shelf_file, protocol=2)
			self.ecobee_service = pyecobee_db[self.thermostat_name]
		except KeyError:
			self.ecobee_service = pyecobee.EcobeeService(thermostat_name=self.thermostat_name, application_key=self.api_key)
		finally:
			#print("Cannot open pyecobee session<br/>\n")
			#print(self.shelf_file)
			pyecobee_db.close()

		if not self.ecobee_service.authorization_token:
			self._authorize()

		if not self.ecobee_service.access_token:
			self._request_tokens()

		now_utc = datetime.datetime.now(pytz.utc)
		if now_utc > self.ecobee_service.refresh_token_expires_on:
			self._authorize()
			self._request_tokens()
		elif now_utc > self.ecobee_service.access_token_expires_on:
			self._refresh_tokens()
		return

	def setLogger(self):
		self.logger = logging.getLogger(__name__)
		out_hdlr = logging.StreamHandler(sys.stdout)
		out_hdlr.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
		out_hdlr.setLevel(logging.INFO)
		self.logger.addHandler(out_hdlr)
		self.logger.setLevel(logging.DEBUG)

	#================================================================
	#================================================================
	# DATA FUNCTIONS TO CALL
	#================================================================
	#================================================================

	def summary_response(self):
		selection=pyecobee.Selection(
			selection_type=pyecobee.SelectionType.REGISTERED.value,
			selection_match=self.thermostat_id,
			include_equipment_status=True)
		thermostat_summary_response = self.ecobee_service.request_thermostats_summary(selection)
		self.logger.info(thermostat_summary_response.pretty_format())
		assert thermostat_summary_response.status.code == 0, 'Failure while executing request_thermostats:\n{0}'.format(
			thermostat_summary_response.pretty_format())

	def sensors(self):
		# Only set the include options you need to True. I've set most of them to True for illustrative purposes only.
		selection = pyecobee.Selection(
			selection_type=pyecobee.SelectionType.REGISTERED.value,
			selection_match=self.thermostat_id,
			include_sensors=True,
		)
		thermostat_response = self._request_data(selection)

		thermostat_obj = thermostat_response.thermostat_list[0]
		self.logger.debug(thermostat_obj.pretty_format())

		sensordict = {}
		for sensor in thermostat_obj.remote_sensors:
			humid = None
			for capability in sensor.capability:
				if capability.type == 'temperature':
					rawtemp = int(capability.value)
					temp = float(rawtemp)/10.
				elif capability.type == 'occupancy':
					occupancy = (capability.value == 'true')
				elif capability.type == 'humidity':
					humid = int(capability.value)
				else:
					print(("Unknown capability: {0}".format(capability.type)))
					sys.exit(1)
			sensordict[sensor.name] = {
				'temperature': temp, 'occupancy': occupancy, 'humidity': humid, 'raw_temp': rawtemp, }
		return sensordict

	def getMedianTemp(self):
		sensordict = self.sensors()
		keys = list(sensordict.keys())
		templist = []
		for name in keys:
			temp = sensordict[name].get('temperature')
			if temp is not None:
				templist.append(temp)
		temparr = numpy.array(templist)
		median_temp = numpy.median(temparr)
		return median_temp


	def weather(self):
		# Only set the include options you need to True. I've set most of them to True for illustrative purposes only.
		selection = pyecobee.Selection(
			selection_type=pyecobee.SelectionType.REGISTERED.value,
			selection_match=self.thermostat_id,
			include_weather=True,
		)
		thermostat_response = self._request_data(selection)
		weather_obj = thermostat_response.thermostat_list[0].weather.forecasts[0]

		self.logger.debug(weather_obj.pretty_format())
		self.logger.debug(dir(weather_obj))
		keys = list(weather_obj.attribute_type_map.keys())
		keys.sort()
		weatherdict = {}
		for key in keys:
			weatherdict[key] = getattr(weather_obj, key)
		return weatherdict

	def equipment_status(self):
		selection = pyecobee.Selection(
			selection_type=pyecobee.SelectionType.REGISTERED.value,
			selection_match=self.thermostat_id,
			include_equipment_status=True,
		)
		thermostat_response = self._request_data(selection)

		thermostat_obj = thermostat_response.thermostat_list[0]
		self.logger.debug(thermostat_obj.pretty_format())
		self.logger.debug(dir(thermostat_obj))

		equipment_status = thermostat_obj.equipment_status.split(',')
		return equipment_status

	def runtime(self):
		selection = pyecobee.Selection(
			selection_type=pyecobee.SelectionType.REGISTERED.value,
			selection_match=self.thermostat_id,
			include_runtime=True,
		)
		thermostat_response = self._request_data(selection)

		thermostat_obj = thermostat_response.thermostat_list[0]
		self.logger.debug(thermostat_obj.pretty_format())
		self.logger.debug(dir(thermostat_obj))

		runtime_obj = thermostat_response.thermostat_list[0].runtime

		self.logger.debug(runtime_obj.pretty_format())
		self.logger.debug(dir(runtime_obj))
		keys = list(runtime_obj.attribute_type_map.keys())
		keys.sort()
		runtimedict = {}
		for key in keys:
			runtimedict[key] = getattr(runtime_obj, key)
		return runtimedict

	def events(self):
		selection = pyecobee.Selection(
			selection_type=pyecobee.SelectionType.REGISTERED.value,
			selection_match=self.thermostat_id,
			include_events=True,
		)
		thermostat_response = self._request_data(selection)

		thermostat_obj = thermostat_response.thermostat_list[0]
		self.logger.debug(thermostat_obj.pretty_format())
		self.logger.debug(dir(thermostat_obj))

		events_list = thermostat_response.thermostat_list[0].events

		events_tree = []
		for event_obj in events_list:
			self.logger.debug(event_obj.pretty_format())
			self.logger.debug(dir(event_obj))
			keys = list(event_obj.attribute_type_map.keys())
			keys.sort()
			eventdict = {}
			for key in keys:
				eventdict[key] = getattr(event_obj, key)
			events_tree.append(eventdict)
		return events_tree


	def everything(self):
		selection = pyecobee.Selection(
				selection_type=pyecobee.SelectionType.REGISTERED.value,
				selection_match=self.thermostat_id,
				include_device=True, include_electricity=True, include_equipment_status=True,
				include_events=True, include_extended_runtime=True, include_house_details=True,
				include_location=True, include_management=True, include_notification_settings=True,
				include_oem_cfg=False, include_privacy=False, include_program=True, include_reminders=True,
				include_runtime=True, include_security_settings=False, include_sensors=True,
				include_settings=True, include_technician=True, include_utility=True, include_version=True,
				include_weather=True, include_alerts=True,)
		thermostat_response = self._request_data(selection)
		self.logger.info(thermostat_response.pretty_format())
		assert thermostat_response.status.code == 0, 'Failure while executing request_thermostats:\n{0}'.format(
				thermostat_response.pretty_format())
		return

	def settings(self):
		selection = pyecobee.Selection(
			selection_type=pyecobee.SelectionType.REGISTERED.value,
			selection_match=self.thermostat_id,
			include_settings=True,
		)
		thermostat_response = self._request_data(selection)

		thermostat_obj = thermostat_response.thermostat_list[0]
		self.logger.debug(thermostat_obj.pretty_format())
		self.logger.debug(dir(thermostat_obj))

		settings_obj = thermostat_response.thermostat_list[0].settings

		self.logger.debug(settings_obj.pretty_format())
		self.logger.debug(dir(settings_obj))
		keys = list(settings_obj.attribute_type_map.keys())
		keys.sort()
		settingsdict = {}
		for key in keys:
			settingsdict[key] = getattr(settings_obj, key)
		return settingsdict

	def startOfNextHour(self):
		now = datetime.datetime.now()
		start_of_next_hour = now.replace(minute=59, second=1, microsecond=0) + datetime.timedelta(seconds=1)
		return start_of_next_hour

	def thirtyPastHour(self):
		now = datetime.datetime.now()
		thirty_past = now.replace(minute=59, second=1, microsecond=0) + datetime.timedelta(minutes=31)
		return thirty_past

	def endOfHour(self):
		now = datetime.datetime.now()
		end_of_hour = now.replace(minute=59, second=1, microsecond=0)
		return end_of_hour

	def setTemperature(self, cooltemp=80, heattemp=55, endTimeMethod='end_of_hour', message=None):
		# Specifically the cooling temperature to use and hold indefinitely
		#HoldType.HOLD_HOURS hold_type=HoldType.HOLD_HOURS, hold_hours=1)
		#update_thermostat_response = self.ecobee_service.set_hold(cool_hold_temp=79, heat_hold_temp=58, hold_type=pyecobee.HoldType.INDEFINITE)
		if endTimeMethod == 'end_of_hour':
			end_time = self.endOfHour()
		elif endTimeMethod == 'start_of_next_hour':
			end_time = self.startOfNextHour()
		elif endTimeMethod == 'thirty_past':
			end_time = self.thirtyPastHour()
		else:
			end_time = self.endOfHour()

		central = pytz.timezone('US/Central')
		update_thermostat_response = self.ecobee_service.set_hold(
			cool_hold_temp=cooltemp,
			heat_hold_temp=heattemp,
			hold_type=pyecobee.HoldType.DATE_TIME,
			end_date_time=central.localize(end_time, is_dst=True), )
		#	hold_type=pyecobee.HoldType.HOLD_HOURS,
		#	hold_hours=holdhours, )
		self.logger.info(update_thermostat_response.pretty_format())
		assert update_thermostat_response.status.code == 0, 'Failure while executing set_hold:\n{0}'.format(
		update_thermostat_response.pretty_format())

	def setHoldClimate(self, climate_setting='away', message=None):
		update_thermostat_response = self.ecobee_service.set_hold(hold_climate_ref='away', hold_type=pyecobee.HoldType.NEXT_TRANSITION)
		self.logger.info(update_thermostat_response.pretty_format())
		assert update_thermostat_response.status.code == 0, 'Failure while executing set_hold:\n{0}'.format(update_thermostat_response.pretty_format())

	def sendMessage(self, ecobeemsg):
		response = self.ecobee_service.send_message(ecobeemsg)
		self.logger.info(response.pretty_format())
		assert response.status.code == 0, 'Failure while executing request_thermostats:\n{0}'.format(response.pretty_format())

if __name__ == "__main__":
	myecobee = MyEcobee()
	myecobee.setLogger()
	myecobee.readThermostatDefs()
	myecobee.openConnection()

	import pprint

	print("\n\nEVENTS\n")
	events_tree = myecobee.events()
	for eventdict in events_tree:
		pprint.pprint(eventdict)
		print('\n')

	print("\n\nSENSORS\n")
	sensordict = myecobee.sensors()
	pprint.pprint(sensordict)

	print("\n\nWEATHER\n")
	weatherdict = myecobee.weather()
	pprint.pprint(weatherdict)

	print("\n\nEQUIPMENT STATUS\n")
	status = myecobee.equipment_status()
	pprint.pprint(status)

	print("\n\nRUNTIME\n")
	status = myecobee.runtime()
	pprint.pprint(status)

	print("\n\nSETTINGS\n")
	status = myecobee.settings()
	pprint.pprint(status)

	#myecobee.sendMessage("Orion is a funny guy")
	#myecobee.setTemperature(cooltemp=71)


