#!/usr/bin/env python3

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

# Decision overview:
# - Pull current and predicted ComEd prices once per loop.
# - Compute a cutoff based on ComEd's reasonable cutoff, then clamp to bounds.
# - If predicted price is very high (2x cutoff after :20), disable for the hour.
# - Otherwise enable if predicted is low, disable if predicted is high, or hold steady.

#badHours = [5, 6, 17, 18]
#badHours = [17, 18]
badHours = []

wemoIpAddresses = [
	"192.168.2.166",  # insight2
]

# Always start charge below this value.
lower_bound = 2.8
# Always stop charge above this value.
upper_bound = 8.2
# Small bias to make the cutoff slightly more permissive or strict.
cutoff_adjust = 0.1
# Deadband around the cutoff to reduce churn.
buffer_rate = 0.5

class ComedSmartWemoPlug(object):
	def __init__(self, ipaddress):
		self.address = ipaddress
		self.depth = 0
		self.connectToWemo()
		return

	#======================================
	def connectToWemo(self):
		self.port = pywemo.ouimeaux_device.probe_wemo(self.address)
		self.wemoUrl = pywemo.setup_url_for_address(self.address)
		self.device = pywemo.discovery.device_from_description(self.wemoUrl)

	#======================================
	def enable(self):
		self.depth += 1
		if self.device.get_state() == 0:
			mystr = f"turning ON wemo plug, start charging ({self.address})"
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
			mystr = f"turning OFF wemo plug, stop charging (state = {self.device.get_state()}, {self.address})"
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
		f.write("%d\t%s\t%s\n"%(time.time(), time.asctime(), f"{self.address}\t{msg}"))
		f.close()

#======================================
def _compute_rates(comlib):
	"""
	Compute current and predicted rates, then derive a bounded cutoff.
	"""
	current_rate = comlib.getCurrentComedRate()
	predict_rate = comlib.getPredictedRate()
	cutoff = comlib.getReasonableCutOff()
	if cutoff < lower_bound:
		cutoff = lower_bound
	elif cutoff > upper_bound:
		cutoff = upper_bound
	cutoff += cutoff_adjust
	return current_rate, predict_rate, cutoff

#======================================
def _decision(now, current_rate, predict_rate, cutoff):
	"""
	Decide whether to enable, disable, or hold based on predicted prices.
	"""
	timestr = "%02d:%02d"%(now.hour, now.minute)
	if predict_rate > 2.0*cutoff and now.minute > 20:
		msg = "%s: charging LONG DISable !! double cutoff ( current %.2f | predict %.2f | cutoff %.2f c/kWh )"%(timestr, current_rate, predict_rate, cutoff)
		return "disable_long", msg

	if predict_rate < lower_bound:
		msg = "%s: charging +enabled ( current %.2f | predict %.2f | cutoff %.2f c/kWh )"%(timestr, current_rate, predict_rate, cutoff)
		return "enable", msg

	if predict_rate > float(cutoff) + buffer_rate:
		msg = "%s: charging -DISabled ( current %.2f | predict %.2f | cutoff %.2f c/kWh )"%(timestr, current_rate, predict_rate, cutoff)
		return "disable", msg

	if predict_rate > upper_bound:
		msg = "%s: charging -DISabled ( %.2f c/kWh | %.2f c/kWh | upper_bound = %.2f c/kWh )"%(timestr, current_rate, predict_rate, upper_bound)
		return "disable", msg

	if predict_rate < float(cutoff) - buffer_rate:
		msg = "%s: charging +enabled ( current %.2f | predict %.2f | cutoff %.2f c/kWh )"%(timestr, current_rate, predict_rate, cutoff)
		return "enable", msg

	msg = "%s: charging ~unchanged ( current %.2f | predict %.2f | cutoff %.2f c/kWh )"%(timestr, current_rate, predict_rate, cutoff)
	return "unchanged", msg

#======================================
def _apply_action(wemo_plugs, action, msg):
	"""
	Apply the decision to every configured plug with a consistent log message.
	"""
	if action == "enable":
		color = "green"
	elif action in ("disable", "disable_long"):
		color = "red"
	else:
		color = "brown"

	for plug in wemo_plugs:
		plug_msg = f"{msg} | {plug.address}"
		print(CL.colorString(plug_msg, color))
		if action == "enable":
			plug.enable()
		elif action in ("disable", "disable_long"):
			plug.disable()
		else:
			pass

#======================================
if __name__ == '__main__':
	count = 0
	last_hour = -2
	refreshTime = 180
	wemo_plugs = []
	for ipaddress in wemoIpAddresses:
		wemo_plug = ComedSmartWemoPlug(ipaddress)
		wemo_plugs.append(wemo_plug)
	comlib = comedlib.ComedLib()
	comlib.msg = False

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

		### always enable before 5AM
		#if hour < 5:
		#	for plug in wemo_plugs:
		#		plug.enable()
		#	continue

		### special condition where it is assumed to be a high price
		if hour in badHours:
			if now.minute < 20:
				mystr = "charging disabled, bad hour, sleep until %d:20"%(hour)
				print(CL.colorString(mystr, "red"))
				for plug in wemo_plugs:
					plug.disable()
				minutesToSleep = 20 - now.minute - 2
				sleepTime = minutesToSleep*60
				if sleepTime > 0:
					time.sleep(sleepTime)
				continue
		else:
			#print "good hour %d"%(hour)
			pass

		current_rate, predict_rate, cutoff = _compute_rates(comlib)
		action, msg = _decision(now, current_rate, predict_rate, cutoff)
		_apply_action(wemo_plugs, action, msg)

		if action == "disable_long":
			minutesToSleep = 60 - now.minute - 2
			sleepTime = minutesToSleep*60
			if sleepTime > 0:
				time.sleep(sleepTime)
			continue
