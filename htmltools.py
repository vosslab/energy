import time
import numpy
import colorsys
import datetime

def numberToHtmlColor(hue, saturation=0.9, value=0.6):
	#input: hue number between 0 and 1
	if hue < 0:
		hue = 0
	if hue > 1:
		hue = 1
	rgbindex = colorsys.hsv_to_rgb(hue, saturation, value)
	r = int(rgbindex[0]*255.)
	g = int(rgbindex[1]*255.)
	b = int(rgbindex[2]*255.)
	colorstr = "rgb({0:d}, {1:d}, {2:d})".format(r, g, b)
	return colorstr

def colorPrice(price, precision=1):
	x_price = numpy.array(
		[-100.,  0.,  3.,  5., 7., 9., 11.,100.],
		dtype=numpy.float64,)
	y_hue = numpy.array(
		[ 315.,240.,180.,120.,60.,15.,5.,  0.],
		dtype=numpy.float64,)
	hue = numpy.interp(price, x_price, y_hue)
	color = numberToHtmlColor(hue/360.)
	if precision == 1:
		text = "<span style='color: {0}'>{1:.1f}&cent;</span>\n".format(color, price)
	elif precision == 2:
		text = "<span style='color: {0}'>{1:.2f}&cent;</span>\n".format(color, price)
	elif precision == 3:
		text = "<span style='color: {0}'>{1:.3f}&cent;</span>\n".format(color, price)
	return text

def colorTemperature(temperature, precision=1):
	x_temp = numpy.array(
		[-100.,  0., 50., 60., 65., 70.,76.,85.,100.,250.],
		dtype=numpy.float64,)
	y_hue = numpy.array(
		[ 330.,270.,240.,210.,180.,170.,90.,30., 10.,  0.],
		dtype=numpy.float64,)
	hue = numpy.interp(temperature, x_temp, y_hue)
	color = numberToHtmlColor(hue/360.)
	if precision == 1:
		text = "<span style='color: {0}'><b>{1:.1f}&deg;</b></span>\n".format(color, temperature)
	elif precision == 2:
		text = "<span style='color: {0}'>{1:.2f}&deg;</span>\n".format(color, temperature)
	elif precision == 3:
		text = "<span style='color: {0}'>{1:.3f}&deg;</span>\n".format(color, temperature)
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
	heatsetting = float(runtimedict['desired_heat'])/10.

	sensordict = myecobee.sensors()
	keys = list(sensordict.keys())
	keys.sort()
	htmltext += "<table style='border: 1px solid darkred; border-spacing: 7px;'>\n"
	htmltext += "<tr><th colspan='4'>Ecobee Thermostats</th></tr>\n"
	htmltext += "<tr><td colspan='4' align='center'>\n"
	htmltext += (("  Current Cool Setting: {0}<br/>\n".format(colorTemperature(coolsetting, 1))))
	htmltext += (("  Current Heat Setting: {0}<br/>\n".format(colorTemperature(heatsetting, 1))))
	htmltext += "</td></tr>\n"
	templist = []
	humidlist = []
	for i,key in enumerate(keys):
		if i % 2 == 0:
			if i > 0:
				htmltext += "</tr>\n"
			htmltext += "<tr>\n"
		htmltext += "   <td>{0}</td>\n".format(key)
		temp = sensordict[key].get('temperature')
		humid = sensordict[key].get('humidity')
		if humid is not None:
			humidlist.append(humid)
		if temp is None:
			continue
		templist.append(temp)
		htmltext += "   <td align='right'>{0}</td>\n".format(colorTemperature(temp, 1))
	htmltext += "</tr>\n"

	htmltext += "<tr><td colspan='4' align='center'>\n"
	humidarr = numpy.array(humidlist)
	avghumid = float(humidarr.mean())
	htmltext += (("  Inside Humidity: {0:.0f}%<br/>\n".format(avghumid)))
	htmltext += "</td></tr>\n"

	htmltext += "<tr><td colspan='4' align='center'>\n"
	temparr = numpy.array(templist)
	avgtemp = float(temparr.mean())
	stdtemp = float(temparr.std())
	htmltext += (("  Average Temperature: {0} &pm; {1:.2f}<br/>\n".format(colorTemperature(avgtemp, 1), stdtemp)))
	htmltext += "</td></tr>\n"

	htmltext += "</table>\n"
	htmltext += "<br/>\n"

	weatherdict = myecobee.weather()
	ordered_key_list = [
			'temperature', 'wind_speed',
			'dewpoint', 'relative_humidity',
			'temp_high', 'temp_low',
		]
	wmap = {
			'temperature': 'temp', 'dewpoint': 'temp',
			'temp_high': 'temp', 'temp_low': 'temp',
			'wind_speed': 'mph', 'relative_humidity': '%',
			'condition': ' ', 'pressure': "<font size='-3'>mm&nbsp;Hg</font>",
		}
	keys = ordered_key_list
	htmltext += "<table style='border: 1px solid darkgreen; border-spacing: 7px;'>\n"
	htmltext += "<tr><th colspan='4'>Ecobee Weather Info</th></tr>\n"
	htmltext += "<tr><td colspan='1'>condition</td>\n"
	htmltext += "    <td colspan='3'>{0}</td></tr>\n".format(weatherdict['condition'])
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

	gas_conversion_rate = 34.7/3.9

	htmltext += "<span style='color: &#35;448844'>24hr Median Rate:"
	median,std = comlib.getMedianComedRate(comed_data)
	htmltext += " {0} &pm; {1:.2f} &cent;</span><br/>".format(colorPrice(median, 1), std)

	htmltext += "&nbsp;<span style='color: &#35;448844'>Equivalent Gas Rate:"
	med_gas_equiv = (median + 3.8) * gas_conversion_rate / 100.
	std_gas_equiv = (std) * gas_conversion_rate / 100.
	htmltext += "</span> ${0:.2f} &pm; {1:.2f} per gallon<br/>".format(med_gas_equiv,std_gas_equiv)

	htmltext += "<span style='color: &#35;444488'>Hour Current Rate:"
	currentRate = comlib.getCurrentComedRate(comed_data)
	htmltext += " {0} </span><br/>".format(colorPrice(currentRate, 3))

	htmltext += "&nbsp;<span style='color: &#35;444488'>Equivalent Gas Rate:"
	gas_equiv = (currentRate + 3.8) * gas_conversion_rate / 100.
	htmltext += "</span> ${0:.2f} per gallon<br/>".format(gas_equiv)

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
	timepoints = max( int(minutes/5), 8)
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

