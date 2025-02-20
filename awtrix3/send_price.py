#!/usr/bin/env python3

# Standard Library
import json
import time

#pypi libraries
import yaml
import numpy
import colorsys
import requests
import datetime
from requests.auth import HTTPBasicAuth

# Local Repo Modules
import comedlib

# AWTRIX Icons Dictionary
awtrix_icons = {
	'power into plug': 40828,
	'STOP': 51783,
	'green box with check': 46832,
	'green check mark': 4474,
	'red x': 270,
	'lightning': 95,
	'green plus': 17093,
	'green arrow up': 120,
	'red arrow down': 124,
	'green arrow down': 402,
	'red arrow up': 4103,
	}

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
	# Price to Hue Mapping (Similar to the HTML version)
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
def get_current_price() -> float:
	"""
	Gets the current electricity price from ComEd API.

	Returns:
		float: Current price in cents.
	"""
	comed = comedlib.ComedLib()
	price = comed.getCurrentComedRate()
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
def draw_arrow(center_x: int, direction: str, color: str=None):
	"""
	Generates drawing instructions for an up or down arrow with a given center pixel.

	Args:
		center_x (int): X position of the center pixel.
		center_y (int): Y position of the center pixel.
		direction (str): "up" or "down" to determine arrow orientation.
		color (str): Color of the arrow in hex format (e.g., "#FF0000").

	Returns:
		list: List of AWTRIX draw commands.
	"""
	if direction == "up":
		#color = up_color if color is None
		arrow_list = [
			{"dl": [center_x, 0, center_x,      5, color]},  # Shaft (1 pixel wide)
			{"dl": [center_x, 0, center_x - 2,  2, color]},  # Left tip
			{"dl": [center_x, 0, center_x + 2,  2, color]}   # Right tip
		]
	elif direction == "down":
		arrow_list = [
			{"dl": [center_x, 0, center_x,      5, color]},  # Shaft (1 pixel wide)
			{"dl": [center_x, 5, center_x - 2,  3, color]},  # Left tip
			{"dl": [center_x, 5, center_x + 2,  3, color]}   # Right tip
		]
	elif direction == "mid":
		arrow_list = [
			{"dl": [center_x-2, 3, center_x+2,  3, color]},  # Shaft (1 pixel wide)
			{"dl": [center_x-2, 3, center_x,    5, color]},  # Left tip
			{"dl": [center_x+2, 3, center_x,    1, color]}   # Right tip
		]
	else:
		raise ValueError("Direction must be 'up' or 'down'.")
	return arrow_list

#============================================
def send_to_awtrix(price: float, trend: str):
	"""
	Sends the electricity price to AWTRIX 3 display.

	Args:
		price (float): The electricity price in cents.
	"""
	# Load credentials from api.yml
	with open("api.yml", "r") as file:
		config = yaml.safe_load(file)

	ip = config["ip"]

	username = config["username"]
	password = config["password"]

	# AWTRIX API details
	awtrix_color = color_price_awtrix(price)

	# Calculate minutes past the hour using time module
	minutes_past_hour = time.localtime().tm_min
	# Convert to percentage
	progress_value = int((minutes_past_hour / 60) * 100)

	# Determine left icon (based on pricing level)
	if price < 2.5:
		left_icon = awtrix_icons['green check mark']
	elif price > 10:
		left_icon = awtrix_icons['red x']
	else:
		left_icon = awtrix_icons['power into plug']

	up_arrow = draw_arrow(29, "up", "#B22222")
	down_arrow = draw_arrow(29, "down", "#228B22")
	mid_arrow = draw_arrow(29, "mid", "#444444")
	if trend == "up":
		arrow = up_arrow
	elif trend == "down":
		arrow = down_arrow
	else:
		arrow = mid_arrow

	data = {
		"name": "PowerPrice",
		"text": f"{price:.1f}¢",
		"icon": left_icon,  # Left-side icon (indicates pricing level)
		"color": awtrix_color,  # Dynamic RGB color
		"progress": progress_value,  # Progress bar (minutes past the hour)
		"repeat": 10,
		"draw": arrow,
		"center": False,  # Disable text centering
	}

	# Send request with authentication
	print(f"Sending to {ip}")
	url = f"http://{ip}/api/custom"
	response = requests.post(url, json=data, auth=HTTPBasicAuth(username, password))

	# Print response for debugging
	print(response.status_code, response.text)

#============================================
def main():
	"""
	Main function to fetch the latest electricity price and send it to AWTRIX.
	"""
	price, trend = get_current_price()

	send_to_awtrix(price, trend)

#============================================
if __name__ == '__main__':
	main()
