#!/usr/bin/env python3

#Traceback manager for CGI scripts
import cgitb
cgitb.enable()

import sys
sys.path.append('/home/pi/energy')

#import notarealmodule

import time
#from energylib import comedlib
from energylib import htmltools
from energylib import solarProduction
#from energylib import ecobeelib


print("Content-Type: text/html\n")
print("<head><title>House Energy Usage</title></head>")

#======================================
print("<body>")
print(f"<h1>House Energy Usage</h1><h3>Current time:</h3>{time.asctime()}<br/>\n")
print("<a href='comed.py'>Show Only Comed Prices</a><br/>")
print("<a href='fullhouse.py'>Show Full House Display with Graphs</a><br/>")


#======================================
#======================================
# Fetch solar data (assuming this is a potentially slow operation)
try:
	solardata = solarProduction.getSolarUsage()
	solar_data_html = "<h3>Solar Data</h3>" + "".join(
		f"{key}: {int(solardata[key]['Value'])/1000.:.3f} k{solardata[key]['Unit']}<br/>"
		for key in solardata if int(solardata[key]['Value']) > 0
	)
	print(solar_data_html)
except Exception as e:
	print("<h3>Solar Data</h3>Failed to load solar data<br/>")
	print(f"Error: {str(e)}<br/>")


#======================================
#======================================
try:
	print(htmltools.htmlEcobee())
	pass
except:
	print('<br/>ECOBEE failed to load, tell Neil')

#======================================
#======================================
print(htmltools.htmlComedData())

#======================================
#======================================
print('<br/>\n')
print('<br/>\n')
print("</body></html>")
