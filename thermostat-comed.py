#!/usr/bin/env python

import sys
import datetime
import comedlib
import ecobeelib

class ThermoStat(object):
	def __init__(self):
		self.hightemp = 80.1
		self.cooltemp = 72.1
		self.comlib = comedlib.ComedLib()
		self.comlib.msg = False
		self.current_rate = None
		self.openEcobee()

	def openEcobee(self):
		self.myecobee = ecobeelib.MyEcobee()
		self.myecobee.setLogger()
		self.myecobee.readThermostatDefs()
		self.myecobee.openConnection()
		self.runtimedict = self.myecobee.runtime()
		self.coolsetting = float(self.runtimedict['desired_cool'])/10.
		print(("Current Cool Setting: {0:.1f}F".format(self.coolsetting)))

	def getRates(self):
		self.current_rate = self.comlib.getCurrentComedRate()
		self.median, self.std = self.comlib.getMedianComedRate()
		self.cutoff = self.comlib.getReasonableCutOff()
		self.predict_rate = self.comlib.getPredictedRate()
		self.recent_rate = self.comlib.getMostRecentRate()

	def showRates(self):
		if self.current_rate is None:
			self.getRates()
		print(("24hr Median Rate: {0:.3f} +/- {1:.3f}c".format(self.median, self.std)))
		print(("Current Rate:     {0:.3f}c".format(self.current_rate)))
		print(("Predicted Rate:   {0:.3f}c".format(self.predict_rate)))
		print(("Cut Off Rate:     {0:.3f}c".format(self.cutoff)))
		print(("Most Recent Rate: {0:.1f}c".format(self.recent_rate)))

	def checkUserOverride(self):
		events_tree = self.myecobee.events()
		user_override = False
		for event_dict in events_tree:
			if not event_dict['end_time'].endswith("01"):
				user_override = True
		return user_override

	def turnOffEcobee(self):
		print("Request: Turn OFF air conditioner")
		if self.coolsetting < self.hightemp - 1:
			print(("Set A/C to {0:.1f} F".format(self.hightemp)))
			self.myecobee.setTemperature(cooltemp=self.hightemp, endTimeMethod='twenty_past')
			#myecobee.sendMessage("A/C was set to 80F, because ComEd Prices are High -- Neil")
		else:
			print("\nnothing to do")

	def turnOnEcobee(self):
		print("Request: Turn ON air conditioner")
		if self.coolsetting > self.cooltemp + 1:
			print("Request: Turn ON air conditioner")
			print(("Set A/C to {0:.1f} F".format(self.cooltemp)))
			self.myecobee.setTemperature(cooltemp=self.cooltemp, endTimeMethod='end_of_hour')
			#myecobee.sendMessage("A/C was set to 80F, because ComEd Prices are High -- Neil")
		else:
			print("\nnothing to do")

if __name__ == "__main__":

	now = datetime.datetime.now()
	if now.hour < 7 or now.hour >= 19:
		print("only run program between 7 am and 7 pm => exit")
		sys.exit(0)

	thermstat = ThermoStat()
	if thermstat.checkUserOverride() is True:
		print("user override in effect => exit")
		sys.exit(0)

	if now.minute <= 20:
		print("less than 20 minutes past the hour => turn off")
		thermstat.turnOffEcobee()
		sys.exit(0)

	thermstat.showRates()
	if thermstat.predict_rate >= thermstat.cutoff:
		thermstat.turnOffEcobee()
	else:
		thermstat.turnOnEcobee()


