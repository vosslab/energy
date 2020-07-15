import time
import numpy

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


def htmlComedData(showPlot=False):
	htmltext = "<h3>Comed Prices</h3>"

	import comedlib
	comlib =	comedlib.ComedLib()
	comlib.msg = False
	comlib.useCache = False
	comed_data = comlib.downloadComedJsonData()
	if comed_data is None:
		htmltext += "comed data failed or not available"
		return htmltext

	htmltext += "<span style='color: &#35;448844'>24hr Median Rate:"
	median,std = comlib.getMedianComedRate(comed_data)
	htmltext += " {0} &pm; {1:.2f} &cent;</span><br/>".format(colorPrice(median, 2), std)

	htmltext += "<span style='color: &#35;444488'>Hour Current Rate:"
	currentRate = comlib.getCurrentComedRate(comed_data)
	htmltext += " {0} </span><br/>".format(colorPrice(currentRate, 2))

	htmltext += "<span style='color: &#35;884444'>Hour Predict Rate:"
	predictRate = comlib.getPredictedRate(comed_data)
	htmltext += " {0} </span><br/>".format(colorPrice(predictRate, 2))

	htmltext += "<span style='color: &#35;448844'>Usage CutOff Rate:"
	cutoffRate = comlib.getReasonableCutOff()
	htmltext += " {0} </span><br/>".format(colorPrice(cutoffRate, 2))

	htmltext += "House Usage Status:\n"
	htmltext += "<table style='display:inline-block; border: 1px solid lightgray; vertical-align:middle;'><tr>\n"
	if predictRate < cutoffRate:
		htmltext += "<td padding=10 bgcolor='darkgreen'><span style='color: white'><b>ON</b>\n"
	else:
		htmltext += "<td padding=10 bgcolor='darkred'><span style='color: white'><b>OFF</b>\n"
	htmltext += "</span></td></tr></table>"
	htmltext += "<br/>\n"

	htmltext += "<span style='color: &#35;666666'>Last Five Rates:\n<ul style='margin: 0 0;'>\n"
	for item in comed_data[:5]:
		timestruct = list(time.localtime(int(item['millisUTC'])/1000.))
		rate = float(item['price'])
		htmltext += "<li>%d:%02d &ndash; %s </li>"%(timestruct[3], timestruct[4], colorPrice(rate))
	htmltext += "</ul></span>"
	htmltext += "<br/>\n"

	hourlyRates = comlib.parseComedData(comed_data)

	htmltext += "<span style='color: &#35;666666'>Hourly Average Rates:\n<ul style='margin: 0 0;'>\n"
	keys = list(hourlyRates.keys())
	keys.sort()
	for key in keys:
		if int(key) < 1:
			continue
		#htmltext += "'%s'<br/>\n"%(key))
		if abs(float(int(key)) - float(key)) > 1e-6:
			continue
		averageRate = numpy.array(hourlyRates[key]).mean()
		hour = int(key)
		#timestruct = list(time.localtime(int(item['millisUTC'])/1000.))
		#rate = float(item['price'])
		htmltext += "<li>%d-%d:00 &ndash; %s </li>"%(hour-1, hour, colorPrice(averageRate, 2))
	htmltext += "</ul></span>"
	htmltext += "<br/>\n"

	htmltext += "<a href='energylib/plot_comed.py'>\n"
	if showPlot is True:
		htmltext += "<img src='energylib/plot_comed.py'>"
		htmltext += "<br/>\n"
	htmltext += "Show Comed Price Plot</a>\n"

	return htmltext

