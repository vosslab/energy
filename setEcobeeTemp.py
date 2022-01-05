#!/usr/bin/env python

import os
import sys
import pytz
import ecobeelib
import argparse

def openEcobee():
	myecobee = ecobeelib.MyEcobee()
	myecobee.setLogger()
	myecobee.readThermostatDefs()
	myecobee.openConnection()
	return myecobee

def setEcobee(args):
	adjustTemp = round(args.temp, 0)
	print("Final Adjusted Temp Setting: {0:.1f}F".format(adjustTemp))

	end_time = datetime.datetime.now()
	end_time = end_time.replace(hour=args.hour, second=1, microsecond=0)
	if args.minute is not None and args.minute > 0:
		end_time = now.replace(minute=args.minute)

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
		help="temperature in degrees Fahrenheit", name="temp",)
	parser.add_argument('-h', '--hour', type=int,   required=True,
		help="end hour in military time", name="hour")
	group = parser.add_mutually_exclusive_group()
	group.add_argument('--heat', action='store_true')
	group.add_argument('--cool', action='store_true')
	args = parser.parse_args()

	setEcobee(args)
