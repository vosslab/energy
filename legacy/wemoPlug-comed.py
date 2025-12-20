#!/usr/bin/env python

import os
import sys
import time
import math
import pywemo
import random
import datetime
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
	sys.path.insert(0, REPO_ROOT)

from energylib import comedlib
from energylib import commonlib

CL = commonlib.CommonLib()

### TODO
# add initial comment to log file
# keep track of length of time charged or off

#badHours = [5, 6, 17, 18]
badHours = [17, 18]
badHours = []
chargingCutoffPrice = 3.99
wemoIpAddresses = [
 "192.168.2.165",
 "192.168.2.168",
]

class ComedSmartWemoPlug(object):
	def __init__(self, ipaddress):
		self.address = ipaddress
		self.connectToWemo()
		self.comlib = comedlib.ComedLib()
		self.comlib.msg = False
		return

	#======================================
	def connectToWemo(self):
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
	def getReasonableCutOff(self):
		return self.comlib.getReasonableCutOff()

	#======================================
	def enable(self):
		if self.device.get_state() == 0:
			mystr = "turning ON wemo plug, start charging"
			print(CL.colorString(mystr, "green"))
			self.device.toggle()
			time.sleep(15)
			self.writeToLogFile("begin charging")
		else:
			#print "charging already active"
			pass
		time.sleep(15)
		if self.device.get_state() == 1:
			return
		print(CL.colorString("ERROR: starting charging", "red"))
		self.enable()
		return

	#======================================
	def disable(self):
		if self.device.get_state() == 1:
			mystr = "turning OFF wemo plug, stop charging"
			print(CL.colorString(mystr, "red"))
			self.device.toggle()
			time.sleep(15)
			self.writeToLogFile("stop charging")
		else:
			#print "charging already disabled"
			pass
		if self.device.get_state() == 0:
			return
		print(CL.colorString("ERROR: turning off charging", "red"))
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
	wemoPlugList = []
	for ipadress in wemoIpAddresses:
		wemoplug = ComedSmartWemoPlug(ipadress)
		wemoPlugList.append(wemoplug)
	while(True):
		if count > 0:
			factor = (math.sqrt(random.random()) + math.sqrt(random.random()))/1.414
			sleepTime = refreshTime*factor
			#print "Sleep %d seconds"%(sleepTime)
			time.sleep(sleepTime)
		count += 1
		now = datetime.datetime.now()
		hour = now.hour
		timestr = "%02d:%02d"%(now.hour, now.minute)

		### always enable before 5AM
		if hour < 5:
			wemoplug.enable()
			continue

		### special condition where it is assumed to be a high price
		if hour in badHours:
			if now.minute < 20:
				mystr = "charging disabled, bad hour, sleep until %d:20"%(hour)
				print(CL.colorString(mystr, "red"))
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
		cutoff = wemoplug.getReasonableCutOff()
		#print("Adjusted cutoff = %.2f ( %.1f | %.1f )"%(cutoff, chargingCutoffPrice, reasonableCutoff))

		#print "rate %.2f"%(rate)
		if rate > 2.0*cutoff and now.minute > 20:
			mystr = "%s: charging LONG disable over double price per kWh ( %.2f | cutoff = %.2f )"%(timestr, rate, cutoff)
			print(CL.colorString(mystr, "red"))
			wemoplug.disable()
			#print "wait out the rest of the hour"
			minutesToSleep = 60 - now.minute - 2
			sleepTime = minutesToSleep*60
			if sleepTime > 0:
				time.sleep(sleepTime)
			continue

		if rate > float(cutoff):
			mystr = "%s: charging disabled, rate too high, %.2f cents per kWh | cutoff = %.2f"%(timestr, rate, cutoff)
			print(CL.colorString(mystr, "red"))
			wemoplug.disable()
			continue

		mystr = "%s: charging enabled ( %.2f kWh | cutoff = %.2f )"%(timestr, rate, cutoff)
		print(CL.colorString(mystr, "green"))
		wemoplug.enable()
