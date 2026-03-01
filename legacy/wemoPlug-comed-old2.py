#!/usr/bin/env python3

import os
import sys
import time
import math
import argparse
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

#============================================
def parse_args():
	"""
	Parse command-line arguments.
	"""
	parser = argparse.ArgumentParser(
		description="Control WeMo plug based on ComEd pricing"
	)
	parser.add_argument(
		'-i', '--wemo-ip', dest='wemo_ip', type=str, default="192.168.2.166",
		help="WeMo plug IP address"
	)
	parser.add_argument(
		'-r', '--refresh-seconds', dest='refresh_seconds', type=int, default=180,
		help="Seconds between pricing refresh checks"
	)
	parser.add_argument(
		'-l', '--lower-bound', dest='lower_bound', type=float, default=2.8,
		help="Always start charge below this price (cents/kWh)"
	)
	parser.add_argument(
		'-u', '--upper-bound', dest='upper_bound', type=float, default=8.2,
		help="Always stop charge above this price (cents/kWh)"
	)
	parser.add_argument(
		'-a', '--cutoff-adjust', dest='cutoff_adjust', type=float, default=0.1,
		help="Adjustment to cutoff price (cents/kWh)"
	)
	args = parser.parse_args()
	return args

#============================================
#badHours = [5, 6, 17, 18]
#badHours = [17, 18]
badHours = []

class ComedSmartWemoPlug(object):
	def __init__(self, wemo_ip):
		self.address = wemo_ip
		self.depth = 0
		self.connectToWemo()
		self.comlib = comedlib.ComedLib()
		self.comlib.msg = False
		return

	#======================================
	def connectToWemo(self):
		self.port = pywemo.ouimeaux_device.probe_wemo(self.address)
		#self.wemoUrl = 'http://%s:%i/setup.xml' % (self.address, self.port)
		self.wemoUrl = pywemo.setup_url_for_address(self.address)
		self.device = pywemo.discovery.device_from_description(self.wemoUrl)

	#======================================
	def getCurrentComedRate(self):
		return self.comlib.getCurrentComedRate()

	#======================================
	def getMedianComedRate(self):
		median,std = self.comlib.getMedianComedRate()
		return median

	#======================================
	def getReasonableCutOff(self):
		return self.comlib.getReasonableCutOff()

	#======================================
	def getPredictedRate(self):
		return self.comlib.getPredictedRate()

	#======================================
	def enable(self):
		self.depth += 1
		if self.device.get_state() == 0:
			mystr = "turning ON wemo plug, start charging"
			print(CL.colorString(mystr, "green"))
			self.device.on()
			time.sleep(15)
			self.writeToLogFile("begin charging")
		else:
			#print "charging already active"
			pass
		time.sleep(5)
		if self.device.get_state() in (1, 8):
			self.depth = 0
			return
		print(f"state = {self.device.get_state()}")
		print(CL.colorString("ERROR: starting charging", "red"))
		if self.depth > 10:
			sys.exit(1)
		else:
			self.enable()
		return

	#======================================
	def disable(self):
		self.depth += 1
		if self.device.get_state() in (1, 8):
			mystr = f"turning OFF wemo plug, stop charging (state = {self.device.get_state()})"
			print(CL.colorString(mystr, "red"))
			self.device.off()
			time.sleep(5)
			self.writeToLogFile("stop charging")
		else:
			#print "charging already disabled"
			pass
		# get state of device
		if self.device.get_state() == 0:
			self.depth = 0
			return
		print(f"state = {self.device.get_state()}")
		print(CL.colorString("ERROR: turning off charging", "red"))
		time.sleep(0.2 * self.depth)
		if self.depth > 10:
			sys.exit(1)
		else:
			self.disable()
		return

	#======================================
	def writeToLogFile(self, msg):
		f = open("car_charging-wemo_log.csv", "a")
		f.write("%d\t%s\t%s\n"%(time.time(), time.asctime(), msg))
		f.close()

#======================================
if __name__ == '__main__':
	args = parse_args()
	count = 0
	last_hour = -2
	refreshTime = args.refresh_seconds
	lower_bound = args.lower_bound
	upper_bound = args.upper_bound
	cutoff_adjust = args.cutoff_adjust
	wemoplug = ComedSmartWemoPlug(args.wemo_ip)
	while(True):
		if count > 0:
			factor = (math.sqrt(random.random()) + math.sqrt(random.random()))/1.414
			sleepTime = refreshTime*factor
			#print "Sleep %d seconds"%(sleepTime)
			time.sleep(sleepTime)
		count += 1
		now = datetime.datetime.now()
		hour = now.hour
		if hour != last_hour:
			print('============== new hour ==')
		last_hour = hour

		timestr = "%02d:%02d"%(now.hour, now.minute)

		### always enable before 5AM
		#if hour < 5:
		#	wemoplug.enable()
		#	continue

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
		current_rate = wemoplug.getCurrentComedRate()
		predict_rate = wemoplug.getPredictedRate()
		median = wemoplug.getMedianComedRate()
		cutoff = wemoplug.getReasonableCutOff()
		### more strict cutoff
		#cutoff = (cutoff + 2.0 * median) / 3.0
		if cutoff < lower_bound:
			cutoff = lower_bound
		elif cutoff > upper_bound:
			cutoff = upper_bound
		### less strict cutoff
		#cutoff += 1.0
		### more strict cutoff
		cutoff += cutoff_adjust

		#print("Adjusted cutoff = %.2f ( %.1f | %.1f )"%(cutoff, chargingCutoffPrice, reasonableCutoff))

		#print(rate)
		#print(median)
		#print(cutoff)
		#print(now.minute)

		if predict_rate > 2.0*cutoff and now.minute > 20:
			mystr = "%s: charging LONG DISable !! double cutoff ( current %.2f | predict %.2f | cutoff %.2f c/kWh )"%(timestr, current_rate, predict_rate, cutoff)
			print(CL.colorString(mystr, "red"))
			wemoplug.disable()
			#print "wait out the rest of the hour"
			minutesToSleep = 60 - now.minute - 2
			sleepTime = minutesToSleep*60
			if sleepTime > 0:
				time.sleep(sleepTime)
			continue

		buffer_rate = 0.5

		if predict_rate < lower_bound:
			mystr = "%s: charging +enabled ( current %.2f | predict %.2f | cutoff %.2f c/kWh )"%(timestr, current_rate, predict_rate, cutoff)
			print(CL.colorString(mystr, "green"))
			wemoplug.enable()

		elif predict_rate > float(cutoff) + buffer_rate:
			mystr = "%s: charging -DISabled ( current %.2f | predict %.2f | cutoff %.2f c/kWh )"%(timestr, current_rate, predict_rate, cutoff)
			print(CL.colorString(mystr, "red"))
			wemoplug.disable()
			continue

		elif predict_rate > upper_bound:
			mystr = "%s: charging -DISabled ( %.2f c/kWh | %.2f c/kWh | upper_bound = %.2f c/kWh )"%(timestr, current_rate, predict_rate, upper_bound)
			print(CL.colorString(mystr, "red"))
			wemoplug.disable()
			continue

		elif predict_rate < float(cutoff) - buffer_rate:
			mystr = "%s: charging +enabled ( current %.2f | predict %.2f | cutoff %.2f c/kWh )"%(timestr, current_rate, predict_rate, cutoff)
			print(CL.colorString(mystr, "green"))
			wemoplug.enable()

		else:
			mystr = "%s: charging ~unchanged ( current %.2f | predict %.2f | cutoff %.2f c/kWh )"%(timestr, current_rate, predict_rate, cutoff)
			print(CL.colorString(mystr, "brown"))
