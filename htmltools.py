import sys
import time
import numpy
import colorsys
import datetime

def numberToHtmlColor(hue, saturation=0.9, value=0.5):
	#input: hue number between 0 and 1
	if hue < 0:
		hue = 0
	if hue > 1:
		hue = 1
	rgbindex = colorsys.hsv_to_rgb(hue, saturation, value)
	print(hue)
	print(rgbindex[0])
	r = int(rgbindex[0]*255.)
	g = int(rgbindex[1]*255.)
	b = int(rgbindex[2]*255.)
	colorstr = "rgb({0:d}, {1:d}, {2:d})".format(r, g, b)
	return colorstr

def colorPrice(price, precision=1):
	x_price = numpy.array(
		[-100.,  0.,  2.,  3., 4., 5.,6.,100.],
		dtype=numpy.float64,)
	y_hue = numpy.array(
		[ 315.,240.,180.,120.,60.,30.,5.,  0.],
		dtype=numpy.float64,)
	hue = numpy.interp(price, x_price, y_hue)
	color = numberToHtmlColor(hue/360.)
	if precision == 1:
		text = "<span style='color: {0}'>{1:.1f}&cent;</span>\n".format(color, price)
	elif precision == 2:
		text = "<span style='color: {0}'>{1:.2f}f&cent;</span>\n".format(color, price)
	elif precision == 3:
		text = "<span style='color: {0}'>{1:.3f}f&cent;</span>\n".format(color, price)
	return text

def colorTemperature(temperature, precision=1):
	x_temp = numpy.array(
		[-100.,  0., 50., 60., 65., 70.,75.,85.,100.,250.],
		dtype=numpy.float64,)
	y_hue = numpy.array(
		[ 330.,270.,240.,120.,180.,170.,90.,30., 10.,  0.],
		dtype=numpy.float64,)
	tarray = numpy.array([temperature,], dtype=numpy.float64)
	hue = numpy.interp(temperature, x_temp, y_hue)
	color = numberToHtmlColor(hue/360.)
	if precision == 1:
		text = "<span style='color: {0}'>{1:.1f}&deg;</span>\n".format(color, temperature)
	elif precision == 2:
		text = "<span style='color: {0}'>{1:.2f}&deg;</span>\n".format(color, temperature)
	elif precision == 3:
		text = "<span style='color: {0}'>{1:.3f}f&deg;</span>\n".format(color, temperature)
	return text

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
		temp = sensordict[key]['temperature']
		htmltext += "   <td align='right'>{0}</td>\n".format(colorTemperature(temp, 1))
	htmltext += "</tr></table>\n"
	htmltext += "<br/>\n"

	weatherdict = myecobee.weather()
	ordered_key_list = [
			'temperature', 'condition', 'dewpoint', 'relative_humidity',
			'temp_high', 'wind_speed', 'temp_low', 'pressure',
		]
	wmap = {
			'temperature': 'temp', 'dewpoint': 'temp',
			'temp_high': 'temp', 'temp_low': 'temp',
			'wind_speed': 'mph', 'relative_humidity': '%',
			'condition': ' ', 'pressure': 'mmHg',
		}
	keys = ordered_key_list
	htmltext += "<table style='border: 1px solid darkgreen; border-spacing: 7px;'>\n"
	htmltext += "<tr><th colspan='4'>Ecobee Weather Info</th></tr>\n"
	for i,key in enumerate(keys):
		if i % 2 == 0:
			if i > 0:
				htmltext += "</tr>\n"
			htmltext += "<tr>\n"
		htmltext += "  <td>{0}</td>\n".format( key.replace('_', ' ') )
		unittype = wmap[key]
		if unittype == 'temp':
			temp = weatherdict[key]/10.
			htmltext += "  <td align='right'>{0}</td>\n".format(colorTemperature(temp, 1))
		else:
			htmltext += "  <td align='right'>{0} {1}</td>\n".format( str(weatherdict[key]), unittype )
	htmltext += "</tr></table>\n"

	return htmltext

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

