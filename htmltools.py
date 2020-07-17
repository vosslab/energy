import time
import numpy
import datetime
import collections

def htmlEcobee():
	htmltext = "<h3>Ecobee Stats</h3>"
	import ecobeelib
	myecobee = ecobeelib.MyEcobee()
	myecobee.setLogger()
	myecobee.readThermostatDefs()
	myecobee.openConnection()
	runtimedict = myecobee.runtime()
	coolsetting = float(runtimedict['desired_cool'])/10.
	htmltext += (("Current Cool Setting: {0:.1f}&deg;F<br/>\n".format(coolsetting)))

	sensordict = myecobee.sensors()
	keys = list(sensordict.keys())
	keys.sort()
	htmltext += "<table style='border: 1px solid darkred; border-spacing: 7px;'>\n"
	htmltext += "<tr><th colspan='4'>Ecobee Thermostats</th></tr>\n"
	for i,key in enumerate(keys):
		if i % 2 == 0:
			if i > 0:
				htmltext += "</tr>\n"
			htmltext += "<tr>\n"
		htmltext += "   <td>{0}</td>\n".format(key)
		htmltext += "   <td>{0:.1f}&deg;</td>\n".format(sensordict[key]['temperature'])
	htmltext += "</tr></table>\n"
	htmltext += "<br/>\n"

	weatherdict = myecobee.weather()
	wmap = collections.OrderedDict({
		'temperature': 'temp', 'dewpoint': 'temp',
		'temp_high': 'temp', 'temp_low': 'temp',
		'wind_speed': 'mph', 'relative_humidity': '%',
		'condition': ' ', 'pressure': 'mmHg',
	})
	keys = list(wmap.keys())
	htmltext += "<table style='border: 1px solid darkgreen; border-spacing: 3px;'>\n"
	htmltext += "<tr><th colspan='4'>Ecobee Weather Info</th></tr>\n"
	for i,key in enumerate(keys):
		if i % 2 == 0:
			if i > 0:
				htmltext += "</tr>\n"
			htmltext += "<tr>\n"
		htmltext += "  <td>{0}</td>\n".format( key.replace('_', ' ') )
		unittype = wmap[key]
		if unittype == 'temp':
			htmltext += "  <td align='right'>{0:.1f}&deg;</td>\n".format(weatherdict[key]/10.)
		else:
			htmltext += "  <td align='right'>{0} {1}</td>\n".format( str(weatherdict[key]), unittype )
	htmltext += "</tr></table>\n"

	return htmltext

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
		text = "<span style='color: %s'>%.1f&cent;</span>\n"%(color, price)
	elif precision == 2:
		text = "<span style='color: %s'>%.2f&cent;</span>\n"%(color, price)
	elif precision == 3:
		text = "<span style='color: %s'>%.3f&cent;</span>\n"%(color, price)
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
	htmltext += " {0} &pm; {1:.2f} &cent;</span><br/>".format(colorPrice(median, 1), std)

	htmltext += "<span style='color: &#35;444488'>Hour Current Rate:"
	currentRate = comlib.getCurrentComedRate(comed_data)
	htmltext += " {0} </span><br/>".format(colorPrice(currentRate, 3))

	htmltext += "<span style='color: &#35;884444'>Hour Predict Rate:"
	predictRate = comlib.getPredictedRate(comed_data)
	htmltext += " {0} </span><br/>".format(colorPrice(predictRate, 3))

	htmltext += "<span style='color: &#35;448844'>Usage CutOff Rate:"
	cutoffRate = comlib.getReasonableCutOff()
	htmltext += " {0} </span><br/>".format(colorPrice(cutoffRate, 3))

	htmltext += "House Usage Status:\n"
	htmltext += "<table style='display:inline-block; border: 1px solid lightgray; vertical-align:middle;'><tr>\n"
	if predictRate < cutoffRate:
		htmltext += "<td padding=10 bgcolor='darkgreen'><span style='color: white'><b>*ON*</b>\n"
	else:
		htmltext += "<td padding=10 bgcolor='darkred'><span style='color: white'><b>.OFF.</b>\n"
	htmltext += "</span></td></tr></table>"
	htmltext += "<br/>\n"

	htmltext += "<table style='border: 1px solid darkblue; border-spacing: 3px; "
	htmltext += "  display: inline-block; vertical-align: top;'>\n"
	htmltext += "<tr><th colspan='2'>Recent Rates</th></tr>\n"
	htmltext += "<tr><th>Time</th><th>Cost</th></tr>\n"
	now = datetime.datetime.now()
	minutes = now.minute
	timepoints = max( int(minutes/5), 5)
	number_of_rows = min( timepoints, len(comed_data) )
	for item in comed_data[:number_of_rows]:
		timestruct = list(time.localtime(int(item['millisUTC'])/1000.))
		rate = float(item['price'])
		#htmltext += "<li>%d:%02d &ndash; %s </li>"%(timestruct[3], timestruct[4], colorPrice(rate))
		htmltext += "<tr>\n"
		htmltext += "  <td align='center'> {0:d}:{1:02d} </td>\n".format(timestruct[3], timestruct[4])
		htmltext += "  <td align='right'> {0} </td>\n".format(colorPrice(rate, 1))
		htmltext += "</tr>\n"
	htmltext += "</table>\n"
	#htmltext += "<br/>\n"
	htmltext += "&nbsp;\n"

	hourlyRates = comlib.parseComedData(comed_data)

	htmltext += "<table style='border: 1px solid darkblue; border-spacing: 3px; "
	htmltext += "  display: inline-block; vertical-align: top;'>\n"
	htmltext += "<tr><th colspan='2'>Hourly Averages</th></tr>\n"
	htmltext += "<tr><th>Range</th><th>Cost</th></tr>\n"
	keys = list(hourlyRates.keys())
	keys.sort()
	keys.reverse()
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
		htmltext += "<tr>\n"
		htmltext += "  <td align='center'> {0:d}-{1:d}:00 </td>\n".format(hour-1, hour)
		htmltext += "  <td align='right'> {0} </td>\n".format(colorPrice(averageRate, 2))
		htmltext += "</tr>\n"
	htmltext += "</table>\n"
	htmltext += "<br/>\n"

	htmltext += "<a href='energylib/plot_comed.py'>\n"
	if showPlot is True:
		htmltext += "<img src='energylib/plot_comed.py'>"
		htmltext += "<br/>\n"
	htmltext += "Show Comed Price Plot</a>\n"

	return htmltext

