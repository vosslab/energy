#!/usr/bin/env python3

#Traceback manager for CGI scripts
import cgitb
cgitb.enable()

import sys
sys.path.append('/home/pi/energy')

import time
from energylib import htmltools
from energylib import solarProduction

print("Content-Type: text/html\n")
print("\n")
print("<head>")
print("<title>House Energy Usage</title>")
print("</head>")

#======================================
print("<body>")
print("<h1>House Energy Usage</h1>")
print("<a href='comed.py'>Show Only Comed Prices</a><br/>")
print("<h3>Current time:</h3>%s"%(time.asctime()))
print('<br/>\n')

#======================================
#======================================
solardata = solarProduction.getSolarUsage()
print("<h3>Solar Data</h3>")
for key in solardata:
	if int(solardata[key]['Value']) > 0:
		print("%s: %.3f k%s<br/>"
			%(key, int(solardata[key]['Value'])/1000., solardata[key]['Unit']))

#======================================
#======================================
print(htmltools.htmlComedData(showPlot=True))

#======================================
#======================================
print('<br/>\n')
print('<br/>\n')
print('<br/>\n')
print("</body></html>")
