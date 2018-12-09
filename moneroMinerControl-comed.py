#!/usr/bin/env python

import time
import json
import math
import numpy
import commonlib
import random
import requests
import datetime
import subprocess

CL = commonlib.CommonLib()

#badHours = [5, 6, 17, 18]
#badHours = [17, 18]
badHours = []
miningCutoffPrice = 3.5

class AutoMonero(object):
	def __init__(self):
		self.monerocmd = "~/devel/monero.sh"
		self.proc = None
		return

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
		ystd = yarray.std()
		if abs(key - float(int(key))) < 0.001:
			print "%03d:00 -> %2.2f +- %2.2f -> %.1f/%.1f"%(key, ymean, ystd, yarray.min(), yarray.max())
			pass
		return ymean+ystd

	def enable(self):
		if self.proc is None:
			cmd = "screen -dmS mine %s"%(self.monerocmd)
			self.proc = True
			subprocess.Popen(cmd, shell=True)
			mystr = "started monero miner, screen -x mine"
			print CL.colorString(mystr, "green")
			return

		print "monero already running, screen -x mine"

	def disable(self):
		if self.proc is not None:
			print CL.colorString("killing miner", "red")
			self.proc = None
			cmd = "pkill xmr-stak"
			subprocess.Popen(cmd, shell=True)
			cmd = "screen -S mine -X quit"
			subprocess.Popen(cmd, shell=True)
		pass

#======================================
if __name__ == '__main__':
	count = 0
	refreshTime = 300
	autominer = AutoMonero()
	while(True):
		if count > 0:
			factor = (math.sqrt(random.random()) + math.sqrt(random.random()))/1.414
			sleepTime = refreshTime*factor 
			#print "Sleep %d seconds"%(sleepTime)
			time.sleep(sleepTime)
		count += 1
		now = datetime.datetime.now()
		hour = now.hour
		if hour in badHours:
			if now.minute < 20:
				mystr = "mining disabled, bad hour, sleep until %d:20"%(hour)
				print CL.colorString(mystr, "red")
				autominer.disable()
				minutesToSleep = 20 - now.minute - 2
				sleepTime = minutesToSleep*60
				if sleepTime > 0:
					time.sleep(sleepTime)
				continue
		else:
			#print "good hour %d"%(hour)
			pass
		rate = autominer.getCurrentComedRate()
		#print "rate %.2f"%(rate)
		if rate > 2.0*miningCutoffPrice and now.minute >20:
			mystr = "mining disable over six cents per kWh ( %.2f )"%(rate)
			print CL.colorString(mystr, "red")
			autominer.disable()
			#print "wait out the rest of the hour"
			minutesToSleep = 60 - now.minute - 2
			sleepTime = minutesToSleep*60
			if sleepTime > 0:
				time.sleep(sleepTime)
			continue
		if rate > float(miningCutoffPrice):
			mystr = "mining disabled, rate too high, %.2f cents per kWh"%(rate)
			print CL.colorString(mystr, "red")

			autominer.disable()

			continue
		print CL.colorString("mining enabled", "green")
		autominer.enable()

