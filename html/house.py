#Traceback manager for CGI scripts
import cgitb
cgitb.enable()

import time
import numpy
from energylib import comedlib
from energylib import htmltools
from energylib import smartReadUsage
from energylib import solarProduction
#from energylib import ecobeelib

def colorPrice(price, precision=1):
	color = "DimGray"
	if price < 0.0:
		color = "RebeccaPurple"
	elif price < 2.0:
		color = "DeepSkyBlue"
	elif price < 3.0:
		color = "SeaGreen"
	elif price < 4.5:
		color = "DarkGoldenRod"
	else:
		color = "DarkRed"
	if precision == 1:
		text = "<span style='color: %s'>%.1f&cent;</span>"%(color, price)
	else:
		text = "<span style='color: %s'>%.2f&cent;</span>"%(color, price)
	return text

print("Content-Type: text/html\n")
print("\n")
print("<head>")
print("<title>House Energy Usage</title>")
print("</head>")

#======================================
print("<body>")
print("<h1>House Energy Usage</h1>")
print("<h3>Current time:</h3>%s"%(time.asctime()))
print('<br/>\n')
print("<a href='comed.py'>Show Only Comed Prices</a><br/>")
print("<a href='fullhouse.py'>Show Full House Display with Graphs</a><br/>")

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
print("<h3>Energy Usage</h3>")
usageText = smartReadUsage.fastReadSmbus()
print("<span style='color: &#35;880000'>Current Usage:")
print(" %s</span><br/>"%(usageText))

#print('<br/>\n')
#print("<img src='energylib/plot_usage.py'>")
print("<a href='energylib/plot_usage.py'>Show Usage Plot</a>")

#======================================
#======================================
print(htmltools.htmlComedData())

#======================================
#======================================
print('<br/>\n')
print('<br/>\n')
print("</body></html>")
