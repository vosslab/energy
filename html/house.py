#Traceback manager for CGI scripts
import cgitb
cgitb.enable()

import time
import numpy
from energylib import comedlib
from energylib import smartReadUsage
from energylib import solarProduction

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
print('<br/>\n')

#print("<img src='energylib/plot_usage.py'>")


#======================================
#======================================
print("<h3>Comed Prices</h3>")
comlib = comedlib.ComedLib()
comlib.msg = False
comlib.useCache = False
comed_data = comlib.downloadComedJsonData()
if comed_data is not None:
	print("<span style='color: &#35;008800'>24hr Median Rate:")
	median,std = comlib.getMedianComedRate(comed_data)
	print(" %s &pm; %.2f &cent;</span><br/>"%(colorPrice(median, 2), std))

	print("<span style='color: &#35;000088'>Hour Predict Rate:")
	predictRate = comlib.getCurrentComedRate(comed_data)
	print(" %s &cent;</span><br/>"%(colorPrice(predictRate, 2)))

	print("<span style='color: &#35;000088'>Usage CutOff Rate:")
	cutoffRate = comlib.getReasonableCutOff()
	print(" %s &cent;</span><br/>"%(colorPrice(cutoffRate, 2)))

	print("House Usage Status:\n")
	print("<table style='display:inline-block; border: 1px solid lightgray; vertical-align:middle;'><tr>\n")
	if predictRate < cutoffRate:
		print("<td padding=10 bgcolor='darkgreen'><span style='color: white'><b>ON</b>\n")
	else:
		print("<td padding=10 bgcolor='darkred'><span style='color: white'><b>OFF</b>\n")
	print("</span></td></tr></table>")
	print('<br/>\n')

	print("<span style='color: &#35;666666'>Last Five Rates:\n<ul style='margin: 0 0;'>\n")
	for item in comed_data[:5]:
		timestruct = list(time.localtime(int(item['millisUTC'])/1000.))
		rate = float(item['price'])
		print("<li>%d:%02d &ndash; %s </li>"%(timestruct[3], timestruct[4], colorPrice(rate)))
	print("</ul></span>")
	#print('<br/>\n')

	hourlyRates = comlib.parseComedData(comed_data)
	print("<span style='color: &#35;000088'>Hour Actual Rate:")
	currRate = numpy.array(hourlyRates[-1]).mean()
	print(" %s &cent;</span><br/>"%(colorPrice(currRate, 2)))
	print('<br/>\n')

	#print('<br/>\n')
	#print("<img src='energylib/plot_comed.py'>")
	#print('<br/>\n')


	print("<span style='color: &#35;666666'>Hourly Average Rates:\n<ul style='margin: 0 0;'>\n")
	keys = hourlyRates.keys()
	keys.sort()
	for key in keys:
		if int(key) < 1:
			continue
		#print("'%s'<br/>\n"%(key))
		if abs(float(int(key)) - float(key)) > 1e-6:
			continue
		averageRate = numpy.array(hourlyRates[key]).mean()
		hour = int(key)
		#timestruct = list(time.localtime(int(item['millisUTC'])/1000.))
		#rate = float(item['price'])
		print("<li>%d-%d:00 &ndash; %s </li>"%(hour-1, hour, colorPrice(averageRate, 2)))
else:
	print("comed data failed or not available")


#======================================
#======================================
print("</body></html>")
