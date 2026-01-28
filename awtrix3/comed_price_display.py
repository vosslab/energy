
#!/usr/bin/env python3

# Standard Library
import os
import sys
import time
import argparse

# PIP3 modules
import yaml
import numpy
import colorsys
import requests

# Local Repo Modules
# Ensure energylib is importable when running this file directly.
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
	sys.path.insert(0, REPO_ROOT)

import icon_draw
from energylib import comedlib

#============================================
# Treat data older than this as unknown for display purposes.
STALE_PRICE_SECONDS = 20 * 60

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
def get_current_price() -> float:
	"""
	Gets the current electricity price from ComEd API.

	Returns:
		float: Current price in cents.
	"""
	comed = comedlib.ComedLib()
	price = comed.getCurrentComedRateUnSafe()
	print(f"Current Power Price: {price:.2f}¢")
	recent = comed.getMostRecentRate()
	print(f"Recent  Power Price: {recent:.1f}¢")
	if recent < price - 0.2:
		trend = "down"
	elif recent > price + 0.2:
		trend = "up"
	else:
		trend = "none"
	print(f"Trend: {trend}")
	return price, trend

#============================================
def compile_comed_price_data():
	"""
	Compile the electricity price to a data dict

	Args:
		price (float): The electricity price in cents.
	"""
	comed = comedlib.ComedLib()
	now_seconds = time.time()
	data = comed.downloadComedJsonData()
	price = None
	trend = "none"
	age_seconds = None
	is_stale = True
	using_previous_hour = False

	if not data:
		print("No ComEd data available")
	else:
		age_seconds = comed.getAgeOfLastPriceSeconds(data, now_seconds)
		if age_seconds is None:
			print("Unable to determine ComEd data age")
		else:
			age_minutes = age_seconds / 60.0
			print(f"Last ComEd data age: {age_minutes:.1f} minutes")

			is_current_hour = comed.isLastPriceFromCurrentHour(data, now_seconds)
			if is_current_hour is None:
				print("Unable to determine last ComEd sample time")
			elif not is_current_hour:
				# Data is from previous hour
				# Check if we're in the first 15 minutes of the current hour
				minutes_past_hour = time.localtime(now_seconds).tm_min
				if minutes_past_hour <= 15:
					# Show previous hour data with indicator
					price = comed.getCurrentComedRateUnSafe(data)
					print(f"Previous Hour Price: {price:.2f}¢ (showing until minute 15)")
					recent = comed.getMostRecentRate(data)
					print(f"Recent  Power Price: {recent:.1f}¢")
					if recent < price - 0.2:
						trend = "down"
					elif recent > price + 0.2:
						trend = "up"
					else:
						trend = "none"
					print(f"Trend: {trend}")
					is_stale = False
					using_previous_hour = True
				else:
					print("ComEd data is from a previous hour (past minute 15)")
			elif age_seconds > STALE_PRICE_SECONDS:
				print(f"ComEd data is stale (> {STALE_PRICE_SECONDS / 60:.0f} minutes)")
			else:
				price = comed.getCurrentComedRateUnSafe(data)
				print(f"Current Power Price: {price:.2f}¢")
				recent = comed.getMostRecentRate(data)
				print(f"Recent  Power Price: {recent:.1f}¢")
				if recent < price - 0.2:
					trend = "down"
				elif recent > price + 0.2:
					trend = "up"
				else:
					trend = "none"
				print(f"Trend: {trend}")
				is_stale = False

	if is_stale:
		if age_seconds is not None:
			stale_minutes = age_seconds / 60.0
			print(f"Displaying unknown price (data age {stale_minutes:.1f} minutes)")
		text_value = "???"
		awtrix_color = [140, 140, 140]
		icon_id = icon_draw.awtrix_icons['red x']
		arrow = arrow_price_awtrix("none")
		progress_color = [140, 140, 140]
	else:
		text_value = f"{price:.1f}¢"
		awtrix_color = color_price_awtrix(price)
		icon_id = icon_price_awtrix(price)
		arrow = arrow_price_awtrix(trend)

		if using_previous_hour:
			# Use orange progress bar to indicate old data
			progress_color = [255, 165, 0]
		else:
			# Use normal color-coded progress bar
			progress_color = awtrix_color

	# AWTRIX API details
	# Use minutes past the hour as a progress bar (0-100%).
	minutes_past_hour = time.localtime().tm_min
	# Convert to percentage
	progress_value = int((minutes_past_hour / 60) * 100)

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

	from requests.auth import HTTPBasicAuth

	config = get_api_config()
	ip = config["ip"]
	username = config["username"]
	password = config["password"]

	app_name = app_data.get("name", "ComedPrice")
	url = f"http://{ip}/api/custom?name={app_name}"

	print(f"Sending to AWTRIX at {ip}...")
	response = requests.post(url, json=app_data, auth=HTTPBasicAuth(username, password))

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
