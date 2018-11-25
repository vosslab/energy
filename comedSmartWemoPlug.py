#!/usr/bin/env python

import time
import json
import math
import numpy
import pywemo
import commonlib
import random
import requests
import datetime
import subprocess

CL = commonlib.CommonLib()

### TODO
# add initial comment to log file
# keep track of length of time charged or off

#badHours = [5, 6, 17, 18]
#badHours = [17, 18]
badHours = []
chargingCutoffPrice = 2.99
wemoIpAddress = "192.168.2.161"

class ComedSmartWemoPlug(object):
	def __init__(self):
		self.connectToWemo()
		return

	#======================================
	def connectToWemo(self):
		self.address = wemoIpAddress
		self.port = pywemo.ouimeaux_device.probe_wemo(self.address)
		self.wemoUrl = 'http://%s:%i/setup.xml' % (self.address, self.port)
		self.device = pywemo.discovery.device_from_description(self.wemoUrl, None)

	#======================================
	def getUrl(self, url):
		fails = 0
		while(fails < 9):
			try:
				resp = requests.get(url, timeout=1)
				break
			except requests.exceptions.ReadTimeout:
				#print "FAILED request"
				fails+=1
				time.sleep(random.random()+ fails**2)
				continue
			except requests.exceptions.ConnectTimeout:
				#print "FAILED connect"
				fails+=2
				time.sleep(random.random()+ fails**2)
				continue

		if fails >= 9:
			print "ERROR: too many failed requests"
			sys.exit(1)
		try:
			data = json.loads(resp.text)
		except ValueError:
			time.sleep(300 + 100*random.random())
			data = self.getUrl(url)
		time.sleep(random.random())
		return data

	#======================================
	def getCurrentComedRate(self):
		comedurl = "https://hourlypricing.comed.com/api?type=5minutefeed"
		data = None
		while data is None:
			data = self.getUrl(comedurl)
		x = []
		yvalues = {}
		y = []
		mintime = int(data[-1]['millisUTC'])
		day = None
		#print "Current Price %.2f"%(float(data[0]['price']))
		for p in data:
			ms = int(p['millisUTC'])
			price = float(p['price'])
			#print ms, price
			timestruct = list(time.localtime(ms/1000.))
			if day is None:
				day = timestruct[2]

			#print timestruct
			hours = timestruct[3] + timestruct[4]/60.
			if timestruct[2] != day:
				hours -= 24.
			hour = int(hours)+1
			hour2 = float(hour) - 0.99
			try:
				yvalues[hour].append(price)
				yvalues[hour2].append(price)
			except KeyError:
				yvalues[hour] = [price,]
				yvalues[hour2] = [price,]
			#hours = (ms - mintime)/1000./60./60.
			x.append(hours)
			y.append(price)

		y2 = []
		x2 = yvalues.keys()
		x2.sort()

		key = x2[-1]
		ylist = yvalues[key]
		yarray = numpy.array(ylist, dtype=numpy.float64)
		ymean = yarray.mean()
		ypositive = numpy.where(yarray < 1.0, 1.0, yarray)
		ystd = ypositive.std()
		weight = (13-len(ylist))/13.
		if abs(key - float(int(key))) < 0.001:
			print "%03d:00 -> %2.2f +- %2.2f / %2.2f -> %.1f/%.1f"%(key, ymean, ystd, ystd*weight, yarray.min(), yarray.max())
			pass
		return ymean + ystd*weight

	#======================================
	def enable(self):
		if self.device.get_state() == 0:
			mystr = "turning ON wemo plug, start charging"
			print CL.colorString(mystr, "green")
			self.device.toggle()
			time.sleep(15)
			self.writeToLogFile("begin charging")
		else:
			print "charging already active"
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
			print "charging already disabled"
		if self.device.get_state() == 0:
			return
		print CL.colorString("ERROR: turning off charging", "red")
		self.disable()
		return

	#======================================
	def writeToLogFile(self, msg):
		f = open("wemo_car_charging-log.csv", "a")
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
		#print "rate %.2f"%(rate)
		if rate > 2.0*chargingCutoffPrice and now.minute > 20:
			mystr = "charging disable over six cents per kWh ( %.2f )"%(rate)
			print CL.colorString(mystr, "red")
			wemoplug.disable()
			#print "wait out the rest of the hour"
			minutesToSleep = 60 - now.minute - 2
			sleepTime = minutesToSleep*60
			if sleepTime > 0:
				time.sleep(sleepTime)
			continue

		if rate > float(chargingCutoffPrice):
			mystr = "charging disabled, rate too high, %.2f cents per kWh"%(rate)
			print CL.colorString(mystr, "red")
			wemoplug.disable()
			continue

		print CL.colorString("charging enabled", "green")
		wemoplug.enable()

