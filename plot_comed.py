#!/usr/bin/env python

import io
import sys
import time
import numpy
import comedlib
from matplotlib import use
use('Agg')
from matplotlib import pyplot

#comedurl = "https://hourlypricing.comed.com/api?type=5minutefeed"
testmode = False

if testmode is True:
	print("Content-Type: text/html")
	print("\n")
	print("<title>CGI script output</title>")
	print("<h1>This is my first CGI script</h1>")
	print("<ul>")
	print(("<li> time: %s</li>"%(time.asctime())))

comlib = comedlib.ComedLib()
comlib.msg = testmode
comlib.useCache = False
if testmode: print("<li>import comed</li>")


comedurl = comlib.getUrl()
if testmode: print("<li>getUrl comed</li>")

data = comlib.downloadComedJsonData(comedurl)
if testmode: print("<li>downloaded comed data</li>")

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
if testmode: print("<li>sorted comed data</li>")

y2 = []
x2 = list(yvalues.keys())
x2.sort()
peakvalue = 0
for key in x2:
	ylist = yvalues[key]
	yarray = numpy.array(ylist, dtype=numpy.float64)
	yp = yarray.mean()
	ypstd = yarray.std()
	if yp+ypstd > peakvalue:
		peakvalue = yp+ypstd+0.1
	ypstr = "%2.3f"%(yp)
	if key <= 12:
		keyst = "%02da-%02da"%(key-1, key)
	else:
		keyst = "%02dp-%02dp"%(key-13, key-12)
	y2.append(yp)

if testmode: print("<li>second sort of comed data</li>")

#median, std = comlib.getMedianComedRate()
pyplot.figure(figsize=(6.0, 8.0), dpi=100)
pyplot.ioff()
pyplot.plot(x, y,  '+', color='darkgreen')
pyplot.plot(x2, y2, '-', color='darkblue', mew=0, ms=5, alpha=50)
pyplot.xticks(numpy.arange(int(min(x)/1.)*1, max(x), 1))	
peakvalue = max(peakvalue, 4)
pyplot.ylim(ymin=0, ymax=peakvalue)

if testmode: print("<li>pyplot part one of comed data</li>")

ax = pyplot.gca()
ax.xaxis.grid() # vertical lines
ax.yaxis.grid() # horizontal lines

pyplot.xlabel('Time (hours since midnight)')
pyplot.ylabel('Cents per kW hr')

if testmode: print("<li>pyplot part two of comed data</li>")


format = "png"
pyplot.tight_layout()
#fig = pyplot.figure()
#figdata = io.StringIO()
figdata = io.BytesIO()
pyplot.savefig(figdata, format=format, dpi=100)
if testmode: print("<li>save fig completed</li>")

#if testmode: pyplot.savefig("comed.png", format=format, dpi=200)

if not testmode: print(("Content-Type: image/%s\n"%(format)))
#if not testmode: sys.stdout.write(figdata.getvalue())
if not testmode: sys.stdout.buffer.write(figdata.getvalue())

print(("<li> time: %s</li>"%(time.asctime())))
if testmode: print("<li>ready to write image...</li>")
if testmode: print("</ul>")
if testmode:
	print(("<img src='data:image/png;base64,%s'/>"
		%(figdata.getvalue().encode("base64").strip())))
if testmode: print("</body></html>")


