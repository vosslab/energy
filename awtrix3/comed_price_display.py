#!/usr/bin/env python3

# Standard Library
import os
import sys
import time
import colorsys
import argparse

# PIP3 modules
import yaml
import numpy
import requests
import requests.auth

# Local Repo Modules
# Ensure energylib is importable when running this file directly.
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
	sys.path.insert(0, REPO_ROOT)

import icon_draw
from energylib import comedlib


#============================================
def color_price_awtrix(price: float) -> tuple:
	"""
	Convert price into an AWTRIX-compatible RGB color.

	Args:
		price (float): The electricity price.
		precision (int): Decimal places for price display.

	Returns:
		tuple: (formatted_price: str, awtrix_color: list[int])
	"""
	# Price to hue mapping (hotter prices shift toward red).
	x_price = numpy.array([-100., 0., 3., 5., 7., 9., 11., 100.], dtype=numpy.float64)
	y_hue = numpy.array([315., 240., 180., 120., 60., 15., 5., 0.], dtype=numpy.float64)

	# Interpolate hue value based on price
	hue = numpy.interp(price, x_price, y_hue) / 360.0  # Convert to 0-1 range
	print(f"hue = {hue*360:.1f}")

	# Convert HSV to RGB (HSV: hue, full saturation, full brightness)
	r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
	awtrix_color = [int(r * 255), int(g * 255), int(b * 255)]

	return awtrix_color

#============================================
def icon_price_awtrix(price: float) -> int:
	if price < 0:
		return icon_draw.awtrix_icons['download blue']
	elif price < 3:
		return icon_draw.awtrix_icons['green power plug']
	elif price < 6:
		return icon_draw.awtrix_icons['yellow power plug']
	elif price < 9:
		return icon_draw.awtrix_icons['orange power plug']
	elif price < 12:
		return icon_draw.awtrix_icons['red power plug']
	return icon_draw.awtrix_icons['red x']

#============================================
def arrow_price_awtrix(trend: str) -> list:
	if trend == "up":
		up_arrow = icon_draw.draw_arrow(29, "up", "#B24444")
		return up_arrow
	elif trend == "down":
		down_arrow = icon_draw.draw_arrow(29, "down", "#448B44")
		return down_arrow
	mid_arrow = icon_draw.draw_arrow(29, "mid", "#888888")
	return mid_arrow

#============================================
def compile_comed_price_data(data=None, now_seconds=None):
	"""
	Compile the electricity price to a data dict.

	Args:
		data: ComEd JSON data list; if None, downloads from the API.
		now_seconds: Current time as Unix timestamp; if None, uses time.time().

	Returns:
		dict: AWTRIX payload with keys text, icon, color, progress, progressC, draw, etc.
	"""
	comed = comedlib.ComedLib()
	# Both None preserves production behavior: live download + current time.
	if now_seconds is None:
		now_seconds = time.time()
	if data is None:
		data = comed.downloadComedJsonData()

	price = None
	trend = "none"
	age_seconds = None
	is_stale = True
	using_previous_hour = False

	if not data:
		# No data available from the API
		print("No ComEd data available")
	elif not comed.isPriceDataFresh(data, now_seconds):
		# Data exists but is too old; age used only for the stale-age print below
		age_seconds = comed.getAgeOfLastPriceSeconds(data, now_seconds)
		if age_seconds is not None:
			stale_minutes = age_seconds / 60.0
			print(f"ComEd data is stale (data age {stale_minutes:.1f} minutes)")
		else:
			print("ComEd data is stale (age undeterminable)")
	else:
		# Data is fresh; determine whether it is from the current or previous clock hour
		is_current_hour = comed.isLastPriceFromCurrentHour(data, now_seconds)
		price = comed.getCurrentComedRateUnSafe(data)
		recent = comed.getMostRecentRate(data)
		print(f"Current Power Price: {price:.2f}c")
		print(f"Recent  Power Price: {recent:.1f}c")
		if recent < price - 0.2:
			trend = "down"
		elif recent > price + 0.2:
			trend = "up"
		else:
			trend = "none"
		print(f"Trend: {trend}")
		is_stale = False
		# When the fresh sample is from the prior clock hour, show an orange bar
		using_previous_hour = (is_current_hour is False)
		if using_previous_hour:
			print("Previous hour price (fresh but prior clock hour)")

	if is_stale:
		# Display unknown indicator; recompute age for the progress bar
		age_seconds = comed.getAgeOfLastPriceSeconds(data, now_seconds)
		text_value = "???"
		awtrix_color = [140, 140, 140]
		icon_id = icon_draw.awtrix_icons['red x']
		arrow = arrow_price_awtrix("none")
		progress_color = [140, 140, 140]
	else:
		text_value = f"{price:.1f}c"
		awtrix_color = color_price_awtrix(price)
		icon_id = icon_price_awtrix(price)
		arrow = arrow_price_awtrix(trend)
		if using_previous_hour:
			# Orange progress bar indicates data is from the previous clock hour
			progress_color = [255, 165, 0]
		else:
			# Normal color-coded progress bar
			progress_color = awtrix_color

	# AWTRIX API details
	# Progress bar represents time since last data update (0-60 minutes = 0-100%).
	if age_seconds is not None:
		age_minutes = age_seconds / 60.0
		# Cap at 60 minutes for display purposes
		progress_value = int(min(age_minutes / 60.0, 1.0) * 100)
		print(f"Progress bar: {age_minutes:.1f} minutes since last update ({progress_value}%)")
	else:
		# Fallback to minutes past hour if age is unavailable
		minutes_past_hour = time.localtime(now_seconds).tm_min
		progress_value = int((minutes_past_hour / 60) * 100)
		print(f"Progress bar: using minutes past hour fallback ({progress_value}%)")

	# AWTRIX payload: text, icon, color, and drawing commands.
	data = {
		"name": "ComedPrice",
		"text": text_value,
		"icon": icon_id,
		"color": awtrix_color,  # Dynamic RGB color
		"progress": progress_value,  # Progress bar (minutes past the hour)
		"progressC": progress_color,
		"repeat": 20,
		"draw": arrow,
		"center": False,  # Disable text centering
		"duration": 15,
		"stack": True,
		"lifetime": 120,
	}

	return data

#============================================
def get_api_config() -> dict:
	"""
	Load AWTRIX API configuration from api.yml.

	Returns:
		dict: Config with 'ip', 'username', 'password' keys.
	"""
	config_path = os.path.join(os.path.dirname(__file__), "api.yml")
	with open(config_path, "r") as f:
		config = yaml.safe_load(f)
	return config

#============================================
def send_to_awtrix(app_data: dict) -> bool:
	"""
	Send data to AWTRIX 3 display.

	Args:
		app_data (dict): AWTRIX payload dictionary.

	Returns:
		bool: True if successful, False otherwise.
	"""
	if app_data is None:
		print("No data to send")
		return False

	config = get_api_config()
	ip = config["ip"]
	username = config["username"]
	password = config["password"]

	app_name = app_data.get("name", "ComedPrice")
	url = f"http://{ip}/api/custom?name={app_name}"

	print(f"Sending to AWTRIX at {ip}...")
	auth = requests.auth.HTTPBasicAuth(username, password)
	response = requests.post(url, json=app_data, auth=auth)

	if response.status_code == 200:
		print(f"  Sent successfully: {app_data.get('text', '')}")
		return True
	else:
		print(f"  Failed: {response.status_code} {response.text}")
		return False

#============================================
def parse_args() -> argparse.Namespace:
	"""
	Parse command-line arguments.

	Returns:
		argparse.Namespace: Parsed arguments.
	"""
	parser = argparse.ArgumentParser(
		description="ComEd electricity price display for AWTRIX 3"
	)
	parser.add_argument(
		"-d", "--dry-run", dest="dry_run", action="store_true",
		help="Do not send, just print data"
	)
	parser.set_defaults(dry_run=False)
	args = parser.parse_args()
	return args

#============================================
def main():
	"""
	Main function to fetch the latest electricity price and send it to AWTRIX.
	"""
	args = parse_args()
	comed_data_dict = compile_comed_price_data()
	print(f"\nAWTRIX Data: {comed_data_dict}")
	if not args.dry_run:
		send_to_awtrix(comed_data_dict)

#============================================
if __name__ == '__main__':
	main()
