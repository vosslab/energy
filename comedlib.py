#!/usr/bin/env python

import sys
import time
import json
import numpy
import commonlib
import random
import requests

CL = commonlib.CommonLib()

class ComedLib(object):
	def __init__(self):
		pass
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
			x.append(hours)
			y.append(price)

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


if __name__ == '__main__':
	comedlib = ComedLib()
	comedlib.getCurrentComedRate()
