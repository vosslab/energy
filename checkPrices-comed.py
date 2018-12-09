#!/usr/bin/env python

import time
import json
import numpy
import random
import requests

comedurl = "https://hourlypricing.comed.com/api?type=5minutefeed"
#comedurl = "https://hourlypricing.comed.com/api?type=5minutefeed&datestart=201801030005&dateend=201801032300"
#supplycharge = 3.6
supplycharge = 0.0

#======================================
def getUrl(url):
	fails = 0
	while(fails < 3):
		try:
			resp = requests.get(url, timeout=1)
			break
		except requests.exceptions.ReadTimeout:
			print "FAILED request"
			fails+=1
			time.sleep(random.random()+ fails**2)
			continue
		except requests.exceptions.ConnectTimeout:
			print "FAILED connect"
			fails+=2
			time.sleep(random.random()+ fails**2)
			continue

	if fails >= 3:
		print "ERROR: too many failed requests"
		sys.exit(1)
	data = json.loads(resp.text)
	time.sleep(random.random())
	return data


if __name__ == '__main__':
	data = getUrl(comedurl)
	x = []
	yvalues = {}
	y = []
	mintime = int(data[-1]['millisUTC'])
	day = None
	for p in data:
		ms = int(p['millisUTC'])
		price = float(p['price']) + supplycharge
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
	for key in x2:
		ylist = yvalues[key]
		yarray = numpy.array(ylist, dtype=numpy.float64)
		yp = yarray.mean()
		if abs(key - float(int(key))) < 0.001:
			print "%03d -> %2.2f   +- %2.1f -> %.1f/%.1f"%(key, yp, yarray.std(), yarray.min(), yarray.max())
		y2.append(yp)

	from matplotlib import pyplot
	#pyplot.xkcd()
	#pyplot.plot(x, y,  '+', color='darkgreen', mew=0, ms=5)
	pyplot.plot(x, y,  '+', color='darkgreen')
	pyplot.plot(x2, y2, '-', color='darkblue', mew=0, ms=5, alpha=50)
	pyplot.xticks(numpy.arange(int(min(x)/1.)*1, max(x), 1))	
	pyplot.xlim(xmin=0)

	ax = pyplot.axes()
	ax.xaxis.grid() # vertical lines
	ax.yaxis.grid() # vertical lines

	pyplot.xlabel('Time')
	pyplot.ylabel('Cents per kW hr')
	pyplot.show()
	pyplot.clf()

