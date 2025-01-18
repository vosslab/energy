import math
import time
import numpy
import colorsys
import datetime
from energylib import comedlib

def numberToHtmlColor(hue, saturation=0.9, value=0.6):
	hue = max(0, min(hue, 1))  # Clamp hue between 0 and 1
	r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
	return f"rgb({int(r * 255)}, {int(g * 255)}, {int(b * 255)})"

def colorPrice(price, precision=1):
	x_price = numpy.array([-100., 0., 3., 5., 7., 9., 11., 100.], dtype=numpy.float64)
	y_hue = numpy.array([315., 240., 180., 120., 60., 15., 5., 0.], dtype=numpy.float64)
	hue = numpy.interp(price, x_price, y_hue)
	color = numberToHtmlColor(hue / 360.)
	return f"<span style='color: {color}'>{price:.{precision}f}&cent;</span>\n"

def colorTemperature(temperature, precision=1):
	x_temp = numpy.array([-100., 0., 50., 60., 65., 70., 76., 85., 100., 250.], dtype=numpy.float64)
	y_hue = numpy.array([330., 270., 240., 210., 180., 170., 90., 30., 10., 0.], dtype=numpy.float64)
	hue = numpy.interp(temperature, x_temp, y_hue)
	color = numberToHtmlColor(hue / 360.)
	return f"<span style='color: {color}'><b>{temperature:.{precision}f}&deg;</b></span>\n"


def htmlEcobee(weather=False):
	htmltext = "<h3>Ecobee Stats</h3>"
	import ecobeelib
	myecobee = ecobeelib.MyEcobee()
	myecobee.setLogger()
	myecobee.readThermostatDefs()
	myecobee.openConnection()
	runtimedict = myecobee.runtime()

	# Ensure 'desired_cool' and 'desired_heat' are not None or NaN
	coolsetting = runtimedict.get('desired_cool', -10)
	heatsetting = runtimedict.get('desired_heat', -10)
	coolsetting = float(coolsetting) / 10.
	heatsetting = float(heatsetting) / 10.

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

	for i, key in enumerate(keys):
		if i % 2 == 0:
			if i > 0:
				htmltext += "</tr>\n"
			htmltext += "<tr>\n"
		htmltext += "   <td>{0}</td>\n".format(key)

		temp = sensordict[key].get('temperature')
		humid = sensordict[key].get('humidity')

		# Handle invalid temperature and humidity values
		if humid is not None and not numpy.isnan(humid):
			humidlist.append(humid)

		if temp is not None and not numpy.isnan(temp):
			templist.append(temp)
			htmltext += "   <td align='right'>{0}</td>\n".format(colorTemperature(temp, 1))
		else:
			htmltext += "   <td align='right'>N/A</td>\n"  # Handle missing temperature data

	htmltext += "</tr>\n"

	htmltext += "<tr><td colspan='4' align='center'>\n"
	if humidlist:
		humidarr = numpy.array(humidlist)
		avghumid = float(humidarr.mean())
		htmltext += (("  Inside Humidity: {0:.0f}%<br/>\n".format(avghumid)))
	else:
		htmltext += "  Inside Humidity: N/A<br/>\n"
	htmltext += "</td></tr>\n"

	htmltext += "<tr><td colspan='4' align='center'>\n"
	if templist:
		temparr = numpy.array(templist)
		avgtemp = float(temparr.mean())
		stdtemp = float(temparr.std())
		htmltext += (("  Average Temperature: {0} &pm; {1:.2f}<br/>\n".format(colorTemperature(avgtemp, 1), stdtemp)))
	else:
		htmltext += "  Average Temperature: N/A<br/>\n"
	htmltext += "</td></tr>\n"

	htmltext += "</table>\n"
	htmltext += "<br/>\n"

	# Show weather info if the parameter is True
	if weather:
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
		for i, key in enumerate(keys):
			if i % 2 == 0:
				if i > 0:
					htmltext += "</tr>\n"
				htmltext += "<tr>\n"
			htmltext += "  <td>{0}</td>\n".format(key.replace('_', ' '))

			unittype = wmap[key]
			value = weatherdict.get(key)

			# Handle weather data processing
			if value is None or numpy.isnan(value):
				htmltext += "  <td align='right'>N/A</td>\n"
			elif unittype == 'temp':
				temp = value / 10.
				htmltext += "  <td align='right'>{0}</td>\n".format(colorTemperature(temp, 1))
			else:
				htmltext += "  <td align='right'>{0} {1}</td>\n".format(str(value), unittype)
		htmltext += "</tr></table>\n"

	return htmltext

def htmlComedData(showPlot: bool = False) -> str:
	"""
	Generate HTML content summarizing ComEd electricity pricing data.

	Args:
		showPlot (bool): Whether to include a plot image link in the HTML output.

	Returns:
		str: An HTML-formatted string containing ComEd pricing information.
	"""

	# Initialize HTML output with a header
	htmltext = "<h3>Comed Prices</h3>"

	# Set up the ComEd library instance
	comlib = comedlib.ComedLib()
	comlib.msg = False  # Suppress console messages from the library
	comlib.useCache = False  # Disable caching to ensure fresh data is downloaded

	# Download ComEd JSON data
	comed_data = comlib.downloadComedJsonData()
	if comed_data is None:
		# If no data is available, display an error message in the HTML
		htmltext += "comed data failed or not available"
		return htmltext

	# Generate the status header, including median, current, and predicted rates
	htmltext += _generate_status_header_html(comlib, comed_data)

	# Add a table displaying recent electricity rates
	htmltext += _generate_recent_rates_table(comed_data)

	# Add a table displaying hourly averages
	hourlyRates = comlib.parseComedData(comed_data)
	htmltext += _generate_hourly_averages_table(hourlyRates)

	# Optionally include a plot of ComEd rates as an image in the HTML
	if showPlot:
		htmltext += "<img src='energylib/plot_comed.py'><br/>\n"
	htmltext += "<a href='energylib/plot_comed.py'>Show Comed Price Plot</a>\n"

	return htmltext

#==============
# Helper Subfunctions
#==============

def _generate_status_header_html(comlib, comed_data) -> str:
	"""
	Generate HTML for the status header, which includes:
	- Median electricity rate and its equivalent gas rate
	- Current electricity rate and its equivalent gas rate
	- Predicted electricity rate
	- Usage cutoff rate
	- Status of house electricity usage (ON/OFF)

	Args:
		comlib: An instance of the ComEd library.
		comed_data: JSON data containing ComEd electricity pricing.

	Returns:
		str: HTML-formatted string containing the status header information.
	"""
	# Define gas-to-electricity conversion rate (predefined constant)
	gas_conversion_rate = 34.7 / 3.9

	# Get median and standard deviation of electricity rates
	median, std = comlib.getMedianComedRate(comed_data)
	# Get the current electricity rate
	currentRate = comlib.getCurrentComedRate(comed_data)
	# Get the predicted electricity rate and cutoff rate for usage
	predictRate = comlib.getPredictedRate(comed_data)
	cutoffRate = comlib.getReasonableCutOff()

	# Generate the HTML content
	html = ""
	html += "<span style='color: &#35;448844'>24hr Median Rate:"
	html += f" {colorPrice(median, 1)} &pm; {std:.2f} &cent;</span><br/>"

	html += "&nbsp;<span style='color: &#35;448844'>Equivalent Gas Rate:"
	med_gas_equiv = (median + 3.8) * gas_conversion_rate / 100.0
	std_gas_equiv = std * gas_conversion_rate / 100.0
	html += f"</span> ${med_gas_equiv:.2f} &pm; {std_gas_equiv:.2f} per gallon<br/>"

	html += "<span style='color: &#35;444488'>Hour Current Rate:"
	html += f" {colorPrice(currentRate, 3)} </span><br/>"

	html += "&nbsp;<span style='color: &#35;444488'>Equivalent Gas Rate:"
	gas_equiv = (currentRate + 3.8) * gas_conversion_rate / 100.0
	html += f"</span> ${gas_equiv:.2f} per gallon<br/>"

	html += "<span style='color: &#35;884444'>Hour Predict Rate:"
	html += f" {colorPrice(predictRate, 3)} </span><br/>"

	html += "<span style='color: &#35;448844'>Usage CutOff Rate:"
	html += f" {colorPrice(cutoffRate, 3)} </span><br/>"

	# Display house usage status (ON/OFF) based on predicted vs. cutoff rates
	html += "House Usage Status:\n"
	html += "<table style='display:inline-block; border: 1px solid lightgray; vertical-align:middle;'><tr>\n"
	if predictRate < cutoffRate:
		html += "<td padding=10 bgcolor='darkgreen'><span style='color: white'><b>*ON*</b>\n"
	else:
		html += "<td padding=10 bgcolor='darkred'><span style='color: white'><b>.OFF.</b>\n"
	html += "</span></td></tr></table>"
	html += "<br/>\n"

	return html

def _generate_recent_rates_table(comed_data: list) -> str:
	"""
	Generate an HTML table for recent electricity rates.

	Args:
		comed_data (list): List of ComEd electricity rate data.

	Returns:
		str: HTML-formatted string for the recent rates table.
	"""
	html = ""
	html += "<table style='border: 1px solid darkblue; border-spacing: 3px; "
	html += "  display: inline-block; vertical-align: top;'>\n"
	html += "<tr><th colspan='2'>Recent Rates</th></tr>\n"
	html += "<tr><th>Time</th><th>Cost</th></tr>\n"

	# Calculate rows to display with actual data
	now = datetime.datetime.now()
	minutes = now.minute
	timepoints = max(int(minutes / 5), 8)  # Minimum 8 timepoints, based on 5-minute intervals
	number_of_rows = min(timepoints, len(comed_data))  # Don't exceed the length of available data

	# Display rows with actual data
	for i, item in enumerate(comed_data[:number_of_rows]):
		timestruct = list(time.localtime(int(item['millisUTC']) / 1000.0))
		rate = float(item['price'])
		html += "<tr>\n"
		html += f"  <td align='center'> {timestruct[3]:d}:{timestruct[4]:02d} </td>\n"
		html += f"  <td align='right'> {colorPrice(rate, 1)} </td>\n"
		html += "</tr>\n"

	# Display additional rows in gray if there are more timepoints available
	if len(comed_data) > number_of_rows:
		for i in range(number_of_rows, min(23, len(comed_data))):
			item = comed_data[i]
			timestruct = list(time.localtime(int(item['millisUTC']) / 1000.0))
			rate = float(item['price'])
			html += "<tr style='background-color: lightgray;'>\n"
			html += f"  <td align='center'> {timestruct[3]:d}:{timestruct[4]:02d} </td>\n"
			html += f"  <td align='right'> {colorPrice(rate, 1)} </td>\n"
			html += "</tr>\n"

	html += "</table>\n"
	html += "&nbsp;\n"

	return html


def _generate_hourly_averages_table(hourlyRates: dict) -> str:
	"""
	Generate an HTML table for hourly average electricity rates.

	Args:
		hourlyRates (dict): Dictionary of hourly rates, with keys as hours
		                    and values as lists of rates for each hour.

	Returns:
		str: HTML-formatted string for the hourly averages table.
	"""
	html = "<table style='border: 1px solid darkblue; border-spacing: 3px; "
	html += "  display: inline-block; vertical-align: top;'>\n"
	html += "<tr><th colspan='2'>Hourly Averages</th></tr>\n"
	html += "<tr><th>Range</th><th>Cost</th></tr>\n"

	# Sort hour keys in descending order
	hour_keys = list(hourlyRates.keys())
	hour_keys.sort(reverse=True)

	# Generate rows for hourly averages
	for hour_key in hour_keys:
		# Skip invalid keys that are not close to integers
		if not math.isclose(hour_key, round(hour_key), abs_tol=1e-6):
			continue

		# Calculate average rate for the current hour
		averageRate = numpy.array(hourlyRates[hour_key]).mean()
		hour = int(hour_key)

		# Determine background color for rows after midnight
		if hour < 1:
			bg_color = "lightgray"
			hour += 24  # Adjust hour to represent a full 24-hour format
		else:
			bg_color = "white"

		# Generate HTML for the row
		html += f"<tr style='background-color: {bg_color};'>\n"
		html += f"  <td align='center'> {hour - 1:d}-{hour:d}:00 </td>\n"
		html += f"  <td align='right'> {colorPrice(averageRate, 2)} </td>\n"
		html += "</tr>\n"

	html += "</table>\n"
	html += "<br/>\n"

	return html

