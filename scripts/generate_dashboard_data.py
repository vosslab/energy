#!/usr/bin/env python3

"""
Generate JSON data files for the energy dashboard.

Fetches ComEd pricing, Ecobee thermostat, and solar production data
using existing energylib modules and writes three JSON files atomically.
Each data source is independent -- one failure does not block others.

Designed to run in a tmux loop (see run_all_tmux.sh).
"""

# Standard Library
import os
import sys
import json
import time
import math
import argparse
import datetime

# PIP modules
import numpy

# Determine repo root and add to path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
	sys.path.insert(0, REPO_ROOT)

# local repo modules
from energylib import comedlib
from energylib import ecobeelib
from energylib import solarProduction
from energylib import htmltools

#============================================
def write_json_atomic(filepath: str, data: dict) -> None:
	"""
	Write a JSON file atomically using tmp + os.replace.

	Args:
		filepath: destination path for the JSON file.
		data: dictionary to serialize as JSON.
	"""
	tmp_path = filepath + ".tmp"
	with open(tmp_path, "w") as f:
		json.dump(data, f, indent=2)
	os.replace(tmp_path, filepath)

#============================================
def generate_comed_data() -> dict:
	"""
	Fetch ComEd pricing data and return a dashboard-ready dictionary.

	Returns:
		dict with median, current, predicted rates, recent samples,
		hourly averages, and raw prices for charting.
	"""
	comlib = comedlib.ComedLib()
	comlib.debug = False
	comlib.useCache = False

	comed_data = comlib.downloadComedJsonData()
	if comed_data is None:
		raise RuntimeError("ComEd data download returned None")

	# Compute rates
	median, std = comlib.getMedianComedRate(comed_data)
	current_rate = comlib.getCurrentComedRateUnSafe(comed_data)
	predicted_rate = comlib.getPredictedRate(comed_data)
	cutoff_rate = comlib.getReasonableCutOff()

	# Recent samples (newest first from API)
	now = datetime.datetime.now()
	current_hour = now.hour
	recent_samples = []
	previous_samples = []
	for item in comed_data[:24]:
		ms = int(item['millisUTC'])
		price = float(item['price'])
		timestruct = time.localtime(ms / 1000.0)
		sample = {
			"time_hour": timestruct.tm_hour,
			"time_min": timestruct.tm_min,
			"price": round(price, 2),
		}
		if timestruct.tm_hour == current_hour:
			recent_samples.append(sample)
		else:
			previous_samples.append(sample)

	# Hourly averages from parsed data
	yvalues = comlib.parseComedData(comed_data)
	hourly_averages = []
	for hour_key in sorted(yvalues.keys(), reverse=True):
		# Skip fractional keys (the 0.01 offset duplicates)
		if not math.isclose(hour_key, round(hour_key), abs_tol=1e-6):
			continue
		avg_price = numpy.array(yvalues[hour_key]).mean()
		hour = int(hour_key)
		hourly_averages.append({
			"hour_start": hour - 1,
			"hour_end": hour,
			"avg_price": round(float(avg_price), 3),
		})

	# Raw prices for chart (today only)
	raw_prices = []
	day = None
	for item in comed_data:
		ms = int(item['millisUTC'])
		price = float(item['price'])
		timestruct = time.localtime(ms / 1000.0)
		if day is None:
			day = timestruct.tm_mday
		# Skip data from previous days
		if timestruct.tm_mday != day:
			continue
		hours = timestruct.tm_hour + timestruct.tm_min / 60.0
		raw_prices.append({
			"hours_since_midnight": round(hours, 3),
			"price": round(price, 2),
		})

	result = {
		"generated_at": datetime.datetime.now().isoformat(timespec='seconds'),
		"median_rate": round(float(median), 3),
		"median_std": round(float(std), 3),
		"current_rate": round(float(current_rate), 3),
		"predicted_rate": round(float(predicted_rate), 3),
		"cutoff_rate": round(float(cutoff_rate), 3),
		"recent_samples": recent_samples,
		"previous_samples": previous_samples,
		"hourly_averages": hourly_averages,
		"raw_prices": raw_prices,
	}
	return result

#============================================
def generate_ecobee_data() -> dict:
	"""
	Fetch Ecobee thermostat data and return a dashboard-ready dictionary.

	Returns:
		dict with cool/heat settings, sensor readings, and averages.
	"""
	myecobee = ecobeelib.MyEcobee()
	myecobee.setLogger()
	myecobee.readThermostatDefs()
	myecobee.openConnection()

	runtimedict = myecobee.runtime()
	sensordict = myecobee.sensors()

	# Extract cool/heat settings
	coolsetting = float(runtimedict.get('desired_cool', -100)) / 10.0
	heatsetting = float(runtimedict.get('desired_heat', -100)) / 10.0

	# Build sensor data
	sensors = {}
	templist = []
	humidlist = []
	for name in sorted(sensordict.keys()):
		sensor = sensordict[name]
		temp = sensor.get('temperature')
		humid = sensor.get('humidity')
		entry = {}
		if temp is not None and not numpy.isnan(temp):
			entry["temperature"] = round(float(temp), 1)
			templist.append(temp)
		if humid is not None and not numpy.isnan(humid):
			entry["humidity"] = int(humid)
			humidlist.append(humid)
		sensors[name] = entry

	# Compute averages
	avg_temperature = None
	std_temperature = None
	if templist:
		temparr = numpy.array(templist)
		avg_temperature = round(float(temparr.mean()), 1)
		std_temperature = round(float(temparr.std()), 2)

	avg_humidity = None
	if humidlist:
		humidarr = numpy.array(humidlist)
		avg_humidity = round(float(humidarr.mean()), 0)

	result = {
		"generated_at": datetime.datetime.now().isoformat(timespec='seconds'),
		"cool_setting": round(coolsetting, 1),
		"heat_setting": round(heatsetting, 1),
		"sensors": sensors,
		"avg_temperature": avg_temperature,
		"std_temperature": std_temperature,
		"avg_humidity": avg_humidity,
	}
	return result

#============================================
def generate_solar_data() -> dict:
	"""
	Fetch solar inverter data and return a dashboard-ready dictionary.

	Returns:
		dict with solar production readings.
	"""
	solar_usage = solarProduction.getSolarUsage()
	readings = {}
	for key, val in solar_usage.items():
		value = int(val['Value'])
		if value > 0:
			readings[key] = {
				"value": value,
				"unit": val['Unit'],
			}

	result = {
		"generated_at": datetime.datetime.now().isoformat(timespec='seconds'),
		"is_daytime": solarProduction.isDaytime(),
		"readings": readings,
	}
	return result

#============================================
def parse_args() -> argparse.Namespace:
	"""
	Parse command-line arguments.
	"""
	parser = argparse.ArgumentParser(
		description="Generate JSON data files for the energy dashboard"
	)
	parser.add_argument(
		'-o', '--output-dir', dest='output_dir',
		default='/var/www/html/api',
		help='Directory to write JSON files to',
	)
	parser.add_argument(
		'-d', '--debug', dest='debug',
		action='store_true',
		help='Enable debug output',
	)
	args = parser.parse_args()
	return args

#============================================
def main():
	args = parse_args()

	# Ensure output directory exists
	os.makedirs(args.output_dir, exist_ok=True)

	timestamp = time.strftime("%H:%M:%S")

	# ComEd data
	try:
		comed = generate_comed_data()
		comed_path = os.path.join(args.output_dir, "comed.json")
		write_json_atomic(comed_path, comed)
		print(f"[{timestamp}] comed.json: OK (current={comed['current_rate']:.1f}c, median={comed['median_rate']:.1f}c)")
	except Exception as e:
		print(f"[{timestamp}] comed.json: FAILED - {e}")

	# Ecobee data
	try:
		ecobee = generate_ecobee_data()
		ecobee_path = os.path.join(args.output_dir, "ecobee.json")
		write_json_atomic(ecobee_path, ecobee)
		avg_temp = ecobee['avg_temperature']
		temp_str = f"{avg_temp:.1f}F" if avg_temp is not None else "N/A"
		print(f"[{timestamp}] ecobee.json: OK (avg temp={temp_str})")
	except Exception as e:
		print(f"[{timestamp}] ecobee.json: FAILED - {e}")

	# Static comed.html page (replaces html/generate_comed_html.py)
	comed_html_path = "/var/www/html/comed.html"
	try:
		comed_page = "<!DOCTYPE html>\n<html lang='en'>\n<head>\n"
		comed_page += "    <meta charset='UTF-8'>\n"
		comed_page += "    <meta name='viewport' content='width=device-width, initial-scale=1.0'>\n"
		comed_page += "    <title>Comed Hourly Prices</title>\n"
		comed_page += "<style>\n"
		comed_page += "  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; }\n"
		comed_page += "  @media (prefers-color-scheme: dark) {\n"
		comed_page += "    body { background: #1a1a1a; color: #e0e0e0; }\n"
		comed_page += "    a { color: #88aacc; }\n"
		comed_page += "    table { border-color: #555; }\n"
		comed_page += "    td, th { border-color: #555; }\n"
		comed_page += "  }\n"
		comed_page += "</style>\n"
		comed_page += "</head>\n<body>\n"
		comed_page += "    <h1>Comed Hourly Prices</h1>\n"
		comed_page += "    <a href='dashboard.html'>Full Dashboard</a><br/>\n"
		comed_page += f"    <h3>Current time:</h3> {time.asctime()}\n    <br/>\n"
		comed_page += htmltools.htmlComedData()
		comed_page += "\n</body>\n</html>"
		with open(comed_html_path, "w") as f:
			f.write(comed_page)
		print(f"[{timestamp}] comed.html: OK")
	except Exception as e:
		print(f"[{timestamp}] comed.html: FAILED - {e}")

	# Solar data
	try:
		solar = generate_solar_data()
		solar_path = os.path.join(args.output_dir, "solar.json")
		write_json_atomic(solar_path, solar)
		reading_count = len(solar['readings'])
		print(f"[{timestamp}] solar.json: OK ({reading_count} active readings, daytime={solar['is_daytime']})")
	except Exception as e:
		print(f"[{timestamp}] solar.json: FAILED - {e}")

#============================================
if __name__ == '__main__':
	main()
