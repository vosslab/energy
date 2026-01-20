#!/usr/bin/env python3

#Traceback manager for CGI scripts
import cgitb
cgitb.enable()

import io
import sys
import time
import numpy
from matplotlib import use
use('Agg')
from matplotlib import pyplot

def dict2listpairs(biglist, key, addzero=False):
	mintime = biglist[0]['timepoint']
	x = []
	y = []
	if addzero is True:
		x.append(0.0)
		y.append(0.0)
	for itemdict in biglist:
		yvalue = itemdict[key]
		if yvalue == 0:
			continue
		hours = (itemdict['timepoint'] - mintime)/3600.
		x.append(hours)
		y.append(yvalue)
	yarray = numpy.array(y)
	return x, yarray


#comedurl = "https://hourlypricing.comed.com/api?type=5minutefeed"
testmode = False

if testmode is True:
	print("Content-Type: text/html")
	print("\n")
	print("<title>CGI script output</title>")
	print("<h1>This is my first CGI script</h1>")
	print("<ul>")
	print(("<li> time: %s</li>"%(time.asctime())))

datestamp = time.strftime("%Y-%m%b-%d-%a").lower()
logname = "/home/pi/energy/usage/%s.log"%(datestamp)

if testmode: print("<li>reading log file</li>")

f = open(logname, "r")
datatree = []
for line in f:
	bits = line.split(",")
	dataline = {
		'timepoint': 	int(bits[0]),
		'totalcurrent': int(bits[1]),
		'current1': 	int(bits[2]),
		'current2': 	int(bits[3]),
		'solarcurrent': int(bits[4]),
	}
	datatree.append(dataline)
f.close()

if testmode: print("<li>finished reading log file</li>")
#if testmode: print(datatree)


if testmode: print("<li>sort the data</li>")

x, totalCurrent = dict2listpairs(datatree, 'totalcurrent')
x, current1 = dict2listpairs(datatree, 'current1')
x, current2 = dict2listpairs(datatree, 'current2')
xSolar, solarCurrent = dict2listpairs(datatree, 'solarcurrent', addzero=True)

if testmode: print("<li>finish sort the data</li>")

#median, std = comlib.getMedianComedRate()
pyplot.figure(figsize=(6.0, 8.0), dpi=100)
pyplot.ioff()
pyplot.plot(x, totalCurrent*120/1e6, '.-', color='darkred')
pyplot.plot(xSolar, solarCurrent*120/1e6, '.-', color='darkorange')
pyplot.xticks(numpy.arange(int(min(x)), max(x), 1))
#peakvalue = max(peakvalue, 4)
#pyplot.ylim(ymin=0, ymax=peakvalue)

if testmode: print("<li>pyplot part one of comed data</li>")

ax = pyplot.gca()
ax.xaxis.grid() # vertical lines
ax.yaxis.grid() # horizontal lines
#ax.axis('equal')

pyplot.xlabel('Time (hours since midnight)')
pyplot.ylabel('kW')

if testmode: print("<li>pyplot part two of comed data</li>")

#ratio=2.0
#xleft, xright = ax.get_xlim()
#ybottom, ytop = ax.get_ylim()
#ax.set_aspect(abs((xright-xleft)/(ybottom-ytop))*ratio)

pyplot.tight_layout()

#fig = pyplot.figure()
#figdata = io.StringIO()
format = "png"
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
