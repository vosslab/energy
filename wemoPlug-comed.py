#!/usr/bin/env python

import time
import math
import pywemo
import random
import datetime
import comedlib
import commonlib

CL = commonlib.CommonLib()

### TODO
# add initial comment to log file
# keep track of length of time charged or off

#badHours = [5, 6, 17, 18]
#badHours = [17, 18]
badHours = []
chargingCutoffPrice = 3.99
wemoIpAddress = "192.168.2.165"

class ComedSmartWemoPlug(object):
	def __init__(self):
		self.connectToWemo()
		self.comlib = comedlib.ComedLib()
		self.comlib.msg = False
		return

	#======================================
	def connectToWemo(self):
		self.address = wemoIpAddress
		self.port = pywemo.ouimeaux_device.probe_wemo(self.address)
		self.wemoUrl = 'http://%s:%i/setup.xml' % (self.address, self.port)
		self.device = pywemo.discovery.device_from_description(self.wemoUrl, None)

	#======================================
	def getCurrentComedRate(self):
		return self.comlib.getCurrentComedRate()

	#======================================
	def getMedianComedRate(self):
		return self.comlib.getMedianComedRate()

	#======================================
	def enable(self):
		if self.device.get_state() == 0:
			mystr = "turning ON wemo plug, start charging"
			print CL.colorString(mystr, "green")
			self.device.toggle()
			time.sleep(15)
			self.writeToLogFile("begin charging")
		else:
			#print "charging already active"
			pass
		time.sleep(15)
		if self.device.get_state() == 1:
			return
		print CL.colorString("ERROR: starting charging", "red")
		self.enable()
		return

	#======================================
	def disable(self):
		if self.device.get_state() == 1:
			mystr = "turning OFF wemo plug, stop charging"
			print CL.colorString(mystr, "red")
			self.device.toggle()
			time.sleep(15)
			self.writeToLogFile("stop charging")
		else:
			#print "charging already disabled"
			pass
		if self.device.get_state() == 0:
			return
		print CL.colorString("ERROR: turning off charging", "red")
		self.disable()
		return

	#======================================
	def writeToLogFile(self, msg):
		f = open("car_charging-wemo_log.csv", "a")
		f.write("%d\t%s\t%s\n"%(time.time(), time.asctime(), msg))
		f.close()

#======================================
if __name__ == '__main__':
	count = 0
	refreshTime = 300
	wemoplug = ComedSmartWemoPlug()
	while(True):
		if count > 0:
			factor = (math.sqrt(random.random()) + math.sqrt(random.random()))/1.414
			sleepTime = refreshTime*factor
			#print "Sleep %d seconds"%(sleepTime)
			time.sleep(sleepTime)
		count += 1
		now = datetime.datetime.now()
		hour = now.hour

		### always enable before 5AM
		if hour < 5:
			wemoplug.enable()
			continue

		### special condition where it is assumed to be a high price
		if hour in badHours:
			if now.minute < 20:
				mystr = "charging disabled, bad hour, sleep until %d:20"%(hour)
				print CL.colorString(mystr, "red")
				wemoplug.disable()
				minutesToSleep = 20 - now.minute - 2
				sleepTime = minutesToSleep*60
				if sleepTime > 0:
					time.sleep(sleepTime)
				continue
		else:
			#print "good hour %d"%(hour)
			pass

		### get the comed rate
		rate = wemoplug.getCurrentComedRate()
		median, std = wemoplug.getMedianComedRate()
		reasonableCutoff = median + std/6.

		cutoff = (chargingCutoffPrice+reasonableCutoff)/2.0
		#print("Adjusted cutoff = %.2f ( %.1f | %.1f )"%(cutoff, chargingCutoffPrice, reasonableCutoff))

		#print "rate %.2f"%(rate)
		if rate > 2.0*cutoff and now.minute > 20:
			mystr = "charging LONG disable over double price per kWh ( %.2f | cutoff = %.2f )"%(rate, cutoff)
			print CL.colorString(mystr, "red")
			wemoplug.disable()
			#print "wait out the rest of the hour"
			minutesToSleep = 60 - now.minute - 2
			sleepTime = minutesToSleep*60
			if sleepTime > 0:
				time.sleep(sleepTime)
			continue

		if rate > float(cutoff):
			mystr = "charging disabled, rate too high, %.2f cents per kWh | cutoff = %.2f"%(rate, cutoff)
			print CL.colorString(mystr, "red")
			wemoplug.disable()
			continue

		mystr = "charging enabled ( %.2f kWh | cutoff = %.2f )"%(rate, cutoff)
		print CL.colorString(mystr, "green")
		wemoplug.enable()

