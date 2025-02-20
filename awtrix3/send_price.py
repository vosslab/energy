#!/usr/bin/env python3

# Standard Library

#pypi libraries
import yaml
import requests
from requests.auth import HTTPBasicAuth

# Local Repo Modules
import solar_display
import comed_price_display

#============================================
def send_to_awtrix(data_dict: dict):
	"""
	Sends the data to AWTRIX 3 display.
	"""
	if data_dict is None:
		return

	# Load credentials from api.yml
	with open("api.yml", "r") as file:
		config = yaml.safe_load(file)

	username = config["username"]
	password = config["password"]
	ip = config["ip"]

	# Send request with authentication
	print(f"Sending data to {ip}")
	url = f"http://{ip}/api/custom"
	response = requests.post(url, json=data_dict, auth=HTTPBasicAuth(username, password))

	# Print response for debugging
	print(response.status_code, response.text)

#============================================
def compile_comed_price_data():
	"""
	Compile the electricity price to a data dict

	Args:
		price (float): The electricity price in cents.
	"""
	price, trend = get_current_price()

	# AWTRIX API details
	awtrix_color = color_price_awtrix(price)

	# Calculate minutes past the hour using time module
	minutes_past_hour = time.localtime().tm_min
	# Convert to percentage
	progress_value = int((minutes_past_hour / 60) * 100)

	# Determine left icon (based on pricing level)
	if price < 2.5:
		left_icon = icon_draw.awtrix_icons['green check mark']
	elif price > 10:
		left_icon = icon_draw.awtrix_icons['red x']
	else:
		left_icon = icon_draw.awtrix_icons['power into plug']

	up_arrow = icon_draw.draw_arrow(29, "up", "#B22222")
	down_arrow = icon_draw.draw_arrow(29, "down", "#228B22")
	mid_arrow = icon_draw.draw_arrow(29, "mid", "#444444")
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

	return data

#============================================
def main():
	"""
	Main function to fetch the latest electricity price and send it to AWTRIX.
	"""
	comed_data_dict = comed_price_display.compile_comed_price_data()
	send_to_awtrix(comed_data_dict)
	solar_data_dict = solar_display.compile_solar_data()
	send_to_awtrix(solar_data_dict)

#============================================
if __name__ == '__main__':
	main()
