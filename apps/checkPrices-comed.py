#!/usr/bin/env python

import os
import sys
import time
import math
import numpy
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
	sys.path.insert(0, REPO_ROOT)

from energylib import comedlib
from energylib import commonlib

#comedurl = "https://hourlypricing.comed.com/api?type=5minutefeed"

if __name__ == '__main__':
	CL = commonlib.CommonLib()
	comlib = comedlib.ComedLib()
	comedurl = comlib.getUrl()
	data = comlib.downloadComedJsonData(comedurl)
	x = []
	yvalues = {}
	y = []
	mintime = int(data[-1]['millisUTC'])
	day = None
	for p in data:
		ms = int(p['millisUTC'])
		price = float(p['price'])
		timestruct = list(time.localtime(ms/1000.))
		if day is None:
			day = timestruct[2]

		#print timestruct
		hours = timestruct[3] + timestruct[4]/60.
		if timestruct[2] != day:
			hours -= 24.
			continue
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
	x2 = list(yvalues.keys())
	x2.sort()
	print("Last 3 prices")
	for i in range(2, -1, -1):
		print("%d:%02d -- %.3f"%(math.floor(x[i]), round((x[i] % 1)*60), y[i]))
	print("")
	peakvalue = 0
	for key in x2:
		ylist = yvalues[key]
		yarray = numpy.array(ylist, dtype=numpy.float64)
		yp = yarray.mean()
		ypstd = yarray.std()
		if yp+ypstd > peakvalue:
			peakvalue = yp+ypstd+0.1
		ypstr = "%2.3f"%(yp)
		if yp < 2:
			ypstr = CL.colorString(ypstr, "cyan")
		elif yp < 3:
			ypstr = CL.colorString(ypstr, "green")
		elif yp < 4:
			ypstr = CL.colorString(ypstr, "yellow")
		else:
			ypstr = CL.colorString(ypstr, "red")
		if key <= 12:
			keyst = "%02da-%02da"%(key-1, key)
		else:
			keyst = "%02dp-%02dp"%(key-13, key-12)
		if abs(key - float(int(key))) < 0.001:
			print(("%s -> %s   +- %2.1f -> %.1f/%.1f (%d)"
				%(keyst, ypstr, ypstd, yarray.min(), yarray.max(), len(yarray))))
		y2.append(yp)
	median, std = comlib.getMedianComedRate()

	from matplotlib import pyplot
	#pyplot.xkcd()
	#pyplot.plot(x, y,  '+', color='darkgreen', mew=0, ms=5)
	pyplot.plot(x, y,  '+', color='darkgreen')
	pyplot.plot(x2, y2, '-', color='darkblue', mew=0, ms=5, alpha=0.5)
	pyplot.xticks(numpy.arange(int(min(x)/1.)*1, max(x), 1))
	#pyplot.xlim(xmin=0)
	peakvalue = max(peakvalue, 4)
	pyplot.ylim(ymin=0, ymax=peakvalue)

	ax = pyplot.gca()
	ax.xaxis.grid() # vertical lines
	ax.yaxis.grid() # horizontal lines

	pyplot.xlabel('Time')
	pyplot.ylabel('Cents per kW hr')
	pyplot.show()
	pyplot.clf()
