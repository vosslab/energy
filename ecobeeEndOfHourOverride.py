#!/usr/bin/env python

import os
import sys
import pytz
import ecobeelib


def openEcobee():
	myecobee = ecobeelib.MyEcobee()
	myecobee.setLogger()
	myecobee.readThermostatDefs()
	myecobee.openConnection()
	return myecobee

def setEcobee(set_temperature):
	adjustTemp = round(set_temperature, 0)
	print("Final Adjusted Cool Setting: {0:.1f}F".format(adjustTemp))

	myecobee = openEcobee()
	print("Request: Turn ON air conditioner")
	print(("Set A/C to {0:.1f} F".format(adjustTemp)))
	myecobee.setTemperature(cooltemp=adjustTemp, endTimeMethod='end_of_hour')


if __name__ == '__main__':
	if len(sys.argv) < 2:
		print("Usage: ecobeeEndOfHourOverride.py <TEMP>")
	set_temperature = float(sys.argv[1])
	setEcobee(set_temperature)
