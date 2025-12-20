#!/usr/bin/env python3

import sys
import math
import time
import numpy
import datetime
import comedlib
import ecobeelib

class ThermoStat(object):
	def __init__(self):
		self.debug = True
		self.use_humid = True
		self.hightemp = 86.1
		#vacation override
		self.cooltemp = 71.1
		# neil preference
		self.cooltemp = 69.1
		# neil-heather compromise
		self.cooltemp = 70.1
		# super vacation override
		#self.cooltemp = 80.1
		self.comlib = comedlib.ComedLib()
		self.comlib.msg = self.debug
		self.current_rate = None
		self.openEcobee()

	def openEcobee(self):
		self.myecobee = ecobeelib.MyEcobee()
		self.myecobee.setLogger()
		self.myecobee.readThermostatDefs()
		self.myecobee.openConnection()
		self.runtimedict = self.myecobee.runtime()
		self.coolsetting = float(self.runtimedict['desired_cool'])/10.
		#self.coolsetting = 72.0
		#print(("Current Cool Setting: {0:.1f}F".format(self.coolsetting)))

	def getRates(self):
		self.current_rate = self.comlib.getCurrentComedRate()
		self.median, self.std = self.comlib.getMedianComedRate()
		self.cutoff = self.comlib.getReasonableCutOff()
		self.predict_rate = self.comlib.getPredictedRate()
		self.recent_rate = self.comlib.getMostRecentRate()

	def showRates(self):
		if self.current_rate is None:
			self.getRates()
		print((" o 24hr Median Rate: {0:.3f} +/- {1:.3f}c".format(self.median, self.std)))
		print((" o Current Rate:     {0:.3f}c".format(self.current_rate)))
		print((" o Predicted Rate:   {0:.3f}c".format(self.predict_rate)))
		print((" o Cut Off Rate:     {0:.3f}c".format(self.cutoff)))
		print((" o Most Recent Rate: {0:.1f}c".format(self.recent_rate)))

	def checkUserOverride(self):
		events_tree = self.myecobee.events()
		if events_tree is None:
			print('no events to parse -> no override')
			return False
		user_override = False
		if len(events_tree) > 1:
			print('{0} events to parse'.format(len(events_tree)))
		for event_dict in events_tree:
			now = datetime.datetime.now()
			end_date = int(event_dict['end_date'][:4])
			if end_date > now.year + 1:
				continue
			print(" - ", event_dict['cool_hold_temp'], event_dict['is_cool_off'], event_dict['end_time'], event_dict['end_date'])
			if ( event_dict['cool_hold_temp'] % 10 != 1
					and event_dict['is_cool_off'] is False
					and not event_dict['end_time'].endswith("01") ):
				print('^^^^ user override ^^^')
				user_override = True
				return True
		return user_override

	def turnOffEcobee(self):
		now = datetime.datetime.now()
		print("||Request: Turn OFF air conditioner")
		if now.minute <= 20 or self.coolsetting < self.hightemp - 1:
			print(("Set A/C to {0:.1f} F".format(self.hightemp)))
			self.myecobee.setTemperature(cooltemp=self.hightemp, endTimeMethod='thirty_past')
			#myecobee.sendMessage("A/C was set to 80F, because ComEd Prices are High -- Neil")
		else:
			#print("\nnothing to do")
			pass

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
		return rel_humid

	def getHumidAdjustedCoolTemp(self):
		if self.use_humid is False:
			return self.cooltemp
		rel_humid = self.getRelativeHumidity()
		if rel_humid is None:
			return self.cooltemp
		adjustTemp = self.inverseHeatIndex(self.cooltemp, rel_humid)
		#rounding
		adjustTemp = round(adjustTemp, 1)
		print(f" _ Humidity Adjusted Cool Setting: {adjustTemp:.1f}F / Relative humidity: {rel_humid:.1f}%")
		if adjustTemp > self.cooltemp:
			adjustTemp = self.cooltemp
		return adjustTemp

	def turnOnEcobee(self):
		print("||Request: Turn ON air conditioner")
		#adjust for humidity
		adjustTemp = self.getHumidAdjustedCoolTemp()

		#adjust if areas are hotter than others
		stdev_temp = self.myecobee.getStdevTemp()
		adjustment = math.sqrt(stdev_temp)/3.0
		adjustTemp -= adjustment
		print(" _ Adjust temp down by {0:.1f}F for standard deviation of {1:.1f}F".format(adjustment, stdev_temp))

		if now.hour >= 19:
			print(" _ Adjust temperature down 1 degree after 7pm for bedtime")
			adjustTemp -= 1.0

		#rounding
		adjustTemp = round(adjustTemp, 1)
		if int(adjustTemp*10) % 10 == 0:
			adjustTemp += 0.1
		adjustTemp = round(adjustTemp, 1)
		print("Final Adjusted Cool Setting: {0:.1f}F".format(adjustTemp))

		if self.coolsetting > adjustTemp + 1.0:
			print("||Request: Turn ON air conditioner")
			print(("Set A/C to {0:.1f} F".format(adjustTemp)))
			self.myecobee.setTemperature(cooltemp=adjustTemp, endTimeMethod='end_of_hour')
			#myecobee.sendMessage("A/C was set to 80F, because ComEd Prices are High -- Neil")
		else:
			#print("\nnothing to do")
			pass

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
		bonus_rate = 2.0*(median_temp - self.cooltemp)/float(self.hightemp - self.cooltemp)
		bonus_rate = max(0.0, bonus_rate)
		print("Temperature Bonus Rate: {0:.3f}c".format(bonus_rate))
		return bonus_rate




if __name__ == "__main__":

	print("=====================================================")
	print(time.asctime())
	now = datetime.datetime.now()
	print("Current hour: {0:d}".format(now.hour))
	#vacation override
	if now.hour < 6 or now.hour >= 21:
		print("only run program between 6am and 8:59pm => exit")
		sys.exit(0)

	thermstat = ThermoStat()
	if thermstat.checkUserOverride() is True:
		print("user override in effect => exit")
		sys.exit(0)
	print("no user override found")

	#don't change temperature when it is almost the next hour
	next_hour_cutoff = 59
	if now.minute >= next_hour_cutoff:
		print(f"more than {next_hour_cutoff} minutes past the hour => turn off")
		thermstat.turnOffEcobee()
		sys.exit(0)

	#minutes past the hour to start tweaking temperature
	if now.hour < 10 or now.hour >= 18:
		#early late
		time_cutoff = 9
	elif now.weekday() >= 5:
		#weekend
		time_cutoff = 7
	else:
		#default
		time_cutoff = 20
		#time_cutoff = 3
	#vacation override
	#time_cutoff = 20

	#blah
	if now.minute <= time_cutoff:
		print("less than {0:d} minutes past the hour => turn off".format(time_cutoff))
		thermstat.turnOffEcobee()
		sys.exit(0)

	thermstat.showRates()
	bonus_rate = thermstat.getRateBonus()
	bonus_cutoff = thermstat.cutoff + bonus_rate + 1.1
	print("Final Cutoff Rate: {0:.3f}".format(bonus_cutoff))

	predict_rate = thermstat.predict_rate
	del thermstat
	thermstat = ThermoStat()
	if thermstat.checkUserOverride() is True:
		print("user override in effect => exit")
		sys.exit(0)
	print("no user override found")

	if predict_rate >= bonus_cutoff:
		thermstat.turnOffEcobee()
	else:
		thermstat.turnOnEcobee()
