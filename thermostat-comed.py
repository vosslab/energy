#!/usr/bin/env python

import sys
import time
import comedlib
import ecobeelib

if __name__ == "__main__":
	hightemp = 80
	cooltemp = 72

	comlib = comedlib.ComedLib()
	comlib.msg = False
	current_rate = comlib.getCurrentComedRate()
	median, std = comlib.getMedianComedRate()
	cutoff = comlib.getReasonableCutOff()
	print(("24hr Median Rate: {0:.3f} +/- {1:.3f}c".format(median, std)))
	print(("Predicted Rate: {0:.3f}c".format(current_rate)))
	print(("Cut Off Rate: {0:.3f}c".format(cutoff)))

	if time.localtime().tm_min <= 7:
		print("less than 7 minutes past the hour => no change")
		sys.exit(0)

	myecobee = ecobeelib.MyEcobee()
	myecobee.setLogger()
	myecobee.readThermostatDefs()
	myecobee.openConnection()
	runtimedict = myecobee.runtime()
	coolsetting = float(runtimedict['desired_cool'])/10.
	print(("Current Cool Setting: {0:.1f}F".format(coolsetting)))

	if current_rate >= cutoff:
		print("Request: Turn OFF air conditioner")
		if coolsetting < hightemp - 1:
			print(("Set A/C to {0:.1f} F".format(hightemp)))
			myecobee.setTemperature(cooltemp=hightemp)
			#myecobee.sendMessage("A/C was set to 80F, because ComEd Prices are High -- Neil")
		else:
			print("\nnothing to do")
	elif time.localtime().tm_min > 17 and coolsetting > cooltemp + 1:
		print("Request: Turn ON air conditioner")
		print(("Set A/C to {0:.1f} F".format(cooltemp)))
		myecobee.setTemperature(cooltemp=cooltemp)
		#myecobee.sendMessage("A/C was set to 72F, because ComEd Prices are Low -- Neil")
	else:
		print("\nnothing to do")


