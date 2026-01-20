#!/usr/bin/env python3

import os
import sys
import argparse
import datetime
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
	sys.path.insert(0, REPO_ROOT)

from energylib import ecobeelib

def openEcobee():
	myecobee = ecobeelib.MyEcobee()
	myecobee.setLogger()
	myecobee.readThermostatDefs()
	myecobee.openConnection()
	return myecobee

def setEcobee(args):
	adjustTemp = round(args.temp, 0)
	print("Final Adjusted Temp Setting: {0:.1f}F".format(adjustTemp))

	endtime = datetime.datetime.now()
	endtime = endtime.replace(hour=args.hour, second=30, microsecond=0)
	if args.minute is not None:
		endtime = endtime.replace(minute=args.minute)
	print("Selected time is:")
	print(endtime.strftime("%I:%M %p <=> %H:%M on %Y-%m-%d"))

	myecobee = openEcobee()
	if args.heat is True:
		print("Request: Turn ON furnace")
		print(("Set HEAT to {0:.1f} F".format(adjustTemp)))
		myecobee.setHoldTemperature(heattemp=adjustTemp, endtime=endtime)

	if args.cool is True:
		print("Request: Turn ON air conditioner")
		print(("Set A/C to {0:.1f} F".format(adjustTemp)))
		myecobee.setHoldTemperature(cooltemp=adjustTemp, endtime=endtime)


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-T', '--temp', type=float, required=True,
		help="temperature in degrees Fahrenheit", dest="temp",)
	parser.add_argument('-H', '--hour', type=int,   required=True,
		help="end hour in military time", dest="hour")
	parser.add_argument('-M', '--minute', type=int,   required=False,
		help="end minutes at the hour", dest="minute", default=0)
	group = parser.add_mutually_exclusive_group(required=True)
	group.add_argument('--heat', action='store_true')
	group.add_argument('--cool', action='store_true')
	args = parser.parse_args()

	if args.hour < datetime.datetime.now().hour:
		print("USE MILITARY TIME")
		sys.exit(1)

	setEcobee(args)
