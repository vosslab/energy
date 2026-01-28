#!/usr/bin/env python3

import os
import sys
import argparse

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
	sys.path.insert(0, REPO_ROOT)

from energylib import ecobeelib

#============================================
def parse_args():
	"""
	Parse command-line arguments.
	"""
	parser = argparse.ArgumentParser(
		description="Set ecobee temperature until end of current hour"
	)
	parser.add_argument(
		'-t', '--temp', dest='temp', type=float, required=True,
		help="Temperature in degrees Fahrenheit"
	)
	heat_cool_group = parser.add_mutually_exclusive_group(required=True)
	heat_cool_group.add_argument(
		'--heat', dest='heat', action='store_true',
		help="Set heat temperature"
	)
	heat_cool_group.add_argument(
		'--cool', dest='cool', action='store_true',
		help="Set cool temperature"
	)
	args = parser.parse_args()
	return args

#============================================
def openEcobee():
	myecobee = ecobeelib.MyEcobee()
	myecobee.setLogger()
	myecobee.readThermostatDefs()
	myecobee.openConnection()
	return myecobee

#============================================
def setEcobee(args):
	adjustTemp = round(args.temp, 0)
	myecobee = openEcobee()

	if args.heat is True:
		print("Final Adjusted Heat Setting: {0:.1f}F".format(adjustTemp))
		print("Request: Turn ON furnace")
		print("Set HEAT to {0:.1f} F".format(adjustTemp))
		myecobee.setTemperature(heattemp=adjustTemp, endTimeMethod='end_of_hour')

	if args.cool is True:
		print("Final Adjusted Cool Setting: {0:.1f}F".format(adjustTemp))
		print("Request: Turn ON air conditioner")
		print("Set A/C to {0:.1f} F".format(adjustTemp))
		myecobee.setTemperature(cooltemp=adjustTemp, endTimeMethod='end_of_hour')

#============================================
if __name__ == '__main__':
	args = parse_args()
	setEcobee(args)
