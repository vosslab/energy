#!/usr/bin/env python3

# Standard Library
import json
import time

#pypi libraries
import yaml
import numpy
import colorsys
import requests
from requests.auth import HTTPBasicAuth

# Local Repo Modules
import comedlib

awtrix_icons = {
	'power into plug': 40828,
	'STOP': 51783,
	'green box with check': 46832,
	'green check mark': 4474,
	'red x': 270,
	'lightning': 95,
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
	return round(price, 2)

#============================================
def send_to_awtrix(price: float):
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
	url = f"http://{ip}/api/custom"
	awtrix_color = color_price_awtrix(price)

	if price > 10:
		icon = awtrix_icons['red x']
	elif price < 2.5:
		icon = awtrix_icons['green check mark']
	else:
		icon = awtrix_icons['power into plug']

	data = {
		"name": "PowerPrice",
		"text": f"{price}¢",
		"icon": icon,
		"color": awtrix_color,
		"repeat": 3
	}

	# Send request with authentication
	print(f"Sending to {ip}")
	response = requests.post(url, json=data, auth=HTTPBasicAuth(username, password))

	# Print response for debugging
	print(response.status_code, response.text)

#============================================
def main():
	"""
	Main function to fetch the latest electricity price and send it to AWTRIX.
	"""
	price = get_current_price()
	print(f"Current Power Price: {price}¢")
	send_to_awtrix(price)

#============================================
if __name__ == '__main__':
	main()
