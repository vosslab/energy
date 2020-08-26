#!/usr/bin/env python

import sys
import numpy
import datetime
import comedlib
import ecobeelib

class ThermoStat(object):
	def __init__(self):
		self.use_humid = True
		self.hightemp = 84.1
		self.cooltemp = 73.1
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
		if events_tree is None:
			return False
		user_override = False
		for event_dict in events_tree:
			if ( event_dict['cool_hold_temp'] % 10 != 1
					and event_dict['is_cool_off'] is False
					and not event_dict['end_time'].endswith("01") ):
				user_override = True
		return user_override

	def turnOffEcobee(self):
		print("Request: Turn OFF air conditioner")
		if self.coolsetting < self.hightemp - 1:
			print(("Set A/C to {0:.1f} F".format(self.hightemp)))
			self.myecobee.setTemperature(cooltemp=self.hightemp, endTimeMethod='thirty_past')
			#myecobee.sendMessage("A/C was set to 80F, because ComEd Prices are High -- Neil")
		else:
			print("\nnothing to do")

	def getRelativeHumidity(self):
		humidvalues = []
		sensorsdict = self.myecobee.sensors()
		keys = list(sensorsdict.keys())
		for name in keys:
			humid = sensorsdict[name].get('humidity')
			#print(list(sensorsdict[name].keys()))
			if humid is not None:
				humidvalues.append(humid)
		if len(humidvalues) == 0:
			print("Failed to get relative humidity")
			return None

		rel_humid = numpy.array(humidvalues).mean()
		print("Relative humidity: {0:.1f}%".format(rel_humid))
		return numpy.array(humidvalues).mean()

	def getAdjustedCoolTemp(self):
		if self.use_humid is False:
			return self.cooltemp
		rel_humid = self.getRelativeHumidity()
		if rel_humid is None:
			return self.cooltemp
		adjustTemp = self.inverseHeatIndex(self.cooltemp, rel_humid)
		#rounding
		adjustTemp = round(adjustTemp, 1)
		if int(adjustTemp*10) % 10 == 0:
			adjustTemp += 0.1
		adjustTemp = round(adjustTemp, 1)
		print("Adjusted Cool Setting: {0:.1f}F".format(adjustTemp))
		if adjustTemp > self.cooltemp:
			adjustTemp = self.cooltemp
		return adjustTemp

	def turnOnEcobee(self):
		print("Request: Turn ON air conditioner")
		adjustTemp = self.getAdjustedCoolTemp()
		if self.coolsetting > adjustTemp + 1:
			print("Request: Turn ON air conditioner")
			print(("Set A/C to {0:.1f} F".format(adjustTemp)))
			self.myecobee.setTemperature(cooltemp=adjustTemp, endTimeMethod='end_of_hour')
			#myecobee.sendMessage("A/C was set to 80F, because ComEd Prices are High -- Neil")
		else:
			print("\nnothing to do")

	def heatIndex(self, temp, rel_humid):
		heat_index = 1.1 * temp + 0.047 * rel_humid - 10.3
		return heat_index

	def inverseHeatIndex(self, heat_index, rel_humid):
		temp = ( heat_index - 0.047 * rel_humid + 8.5)/1.1
		return temp

	def getRateBonus(self):
		median_temp = self.myecobee.getMedianTemp()
		print("Median House Temp: {0:.1f}F".format(median_temp))
		#self.hightemp = 80.1
		#self.cooltemp = 72.1
		bonus_rate = (median_temp - self.cooltemp)/float(self.hightemp - self.cooltemp)
		bonus_rate = max(0.0, bonus_rate)
		print("Temperature Bonus Rate: {0:.3f}c".format(bonus_rate))
		return bonus_rate


if __name__ == "__main__":

	now = datetime.datetime.now()
	if now.hour < 6 or now.hour >= 20:
		print("only run program between 6am and 8pm => exit")
		sys.exit(0)

	thermstat = ThermoStat()
	if thermstat.checkUserOverride() is True:
		print("user override in effect => exit")
		sys.exit(0)

	if now.hour < 10 or now.hour >= 18 and now.weekday() <= 4:
		time_cutoff = 20
	else:
		time_cutoff = 9

	if now.minute <= time_cutoff:
		print("less than {0:d} minutes past the hour => turn off".format(time_cutoff))
		thermstat.turnOffEcobee()
		sys.exit(0)

	thermstat.showRates()
	bonus_rate = thermstat.getRateBonus()
	bonus_cutoff = thermstat.cutoff + bonus_rate
	print("Final Cutoff Rate: {0:.3f}".format(bonus_cutoff))
	if thermstat.predict_rate >= bonus_cutoff:
		thermstat.turnOffEcobee()
	else:
		thermstat.turnOnEcobee()
