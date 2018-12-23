#!/usr/bin/env python

import os
import sys
import time
import json
import yaml
import numpy
import random
import requests
import datetime

### TODO
# add caching
# take median from last three days

#======================================
#======================================
class ComedLib(object):
	def __init__(self):
		self.msg = True
		self.useCache = True
		scriptdir = os.path.dirname(__file__)
		filename = "comed_cache_file.yml"
		self.cachefile = os.path.join(scriptdir, filename)
		self.baseurl = "https://hourlypricing.comed.com/api?type=5minutefeed"
		#comedurl = "https://hourlypricing.comed.com/api?type=5minutefeed&datestart=201801030005&dateend=201801032300"
		return
	
	#======================================
	def writeCache(self, data):
		if self.useCache is False:
			return
		if self.msg is True:
			print("saving data to %s"%(self.cachefile))
		f = open(self.cachefile, "w")
		fulldata = {
			'timestamp': int(time.time()),
			'data': data,
		}
		yaml.dump(fulldata, f)
		f.close()
		return

	#======================================
	def readCache(self):
		if self.useCache is False:
			return None
		if not os.path.exists(self.cachefile):
			return None
		if self.msg is True:
			print("reading data from %s"%(self.cachefile))
		f = open(self.cachefile, "r")
		fulldata = yaml.load(f)
		f.close()
		if not isinstance(fulldata, dict):
			return None
		if time.time() - fulldata['timestamp'] > 240:
			return None
		return fulldata['data']

	#======================================
	def safeDownloadWebpage(self, url):
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
		return resp

	#======================================
	def downloadComedJsonData(self, url=None):
		data = self.readCache()
		if isinstance(data, list):
			if self.msg is True:
				print("Using comed data from cache")
			return data
		else:
			if self.msg is True:
				print("Downloading comed new data")
		if url is None:
			url = self.getUrl()
		resp = self.safeDownloadWebpage(url)
		try:
			data = json.loads(resp.text)
		except ValueError:
			time.sleep(300 + 100*random.random())
			data = self.downloadComedJsonData(url)
		self.writeCache(data)
		time.sleep(random.random())
		return data

	#======================================
	def getUrl(self):
		return self.baseurl

	#======================================
	def getHourUrl(self):
		return self.getUrl()
		### this does not work to limit data
		#now = datetime.datetime.now()
		#timecode = "%04d%02d%02d%02d00"%(now.year, now.month, now.day, now.hour)
		#print timecode
		#adding timecode does not work to limit data return, only good for past dates, e.g., 2014
		#comedurl = self.baseurl #+"&datestart="+timecode
		#return comedurl

	#======================================
	def parseComedData(self, data=None):
		if data is None:
			return None
		#x = []
		#y = []
		yvalues = {}
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
			#x.append(hours)
			#y.append(price)
		return yvalues

	#======================================
	def getCurrentComedRate(self, data=None):
		while data is None:
			data = self.downloadComedJsonData()
		yvalues = self.parseComedData(data)
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
			if self.msg is True:
				print("%03d:00 -> %2.2f +- %2.2f / %2.2f -> %.1f/%.1f"
					%(key, ymean, ystd, ystd*weight, yarray.min(), yarray.max()))
			pass
		return ymean + ystd*weight

	#======================================
	def getMedianComedRate(self, data=None):
		while data is None:
			data = self.downloadComedJsonData()
		prices = []
		for item in data:
			prices.append(float(item['price']))
		parray = numpy.array(prices, dtype=numpy.float64)
		median = numpy.median(parray)
		std = numpy.std(parray)
		if self.msg is True:
			print("24 hour median price: %.3f +/- %.3f"%(median, std))
		return median, std

#======================================
#======================================
if __name__ == '__main__':
	comedlib = ComedLib()
	comedlib.getCurrentComedRate()