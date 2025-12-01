#!/usr/bin/env python3

# Standard Library
import time
import random

#pypi libraries
import yaml
import requests
from requests.auth import HTTPBasicAuth

# Local Repo Modules
import solar_display
import comed_price_display
import display_date

#============================================
def get_active_awtrix_apps():
	"""
	Fetches and lists the currently active apps on AWTRIX 3.
	"""
	# Load credentials from api.yml
	with open("api.yml", "r") as file:
		config = yaml.safe_load(file)

	username = config["username"]
	password = config["password"]
	ip = config["ip"]

	# API URL for getting active apps
	url = f"http://{ip}/api/loop"

	try:
		response = requests.get(url, auth=HTTPBasicAuth(username, password))

		if response.status_code == 200:
				apps = response.json()  # Convert response to dictionary
				print("\nActive AWTRIX Apps:")
				for app_name, position in apps.items():
					#print(f"  - {app_name}: Slot {position}")
					print(f"  - Slot {position}: {app_name}")
		else:
				print(f"Failed to fetch AWTRIX apps! Status Code: {response.status_code}")
	except Exception as e:
		print(f"⚠Error fetching AWTRIX apps: {e}")

#============================================
def send_to_awtrix(app_data: dict):
	"""
	Sends the data to AWTRIX 3 display.
	"""
	if app_data is None:
		return

	# Load credentials from api.yml
	with open("api.yml", "r") as file:
		config = yaml.safe_load(file)

	username = config["username"]
	password = config["password"]
	ip = config["ip"]

	# Send request with authentication
	#print(f"Sending data to {ip}")
	print(f"Sending {len(app_data)} data packets to {ip}")
	#url = f"http://{ip}/api/custom"
	app_name = app_data["name"]  # Extract app name
	url = f"http://{ip}/api/custom?name={app_name}"  # Add app name to URL
	try:
		print(f"  NAME: '{app_data.get('name', '')}'")
		print(f"  TEXT: '{app_data.get('text', '')}'")
	except AttributeError:
		pass
	response = requests.post(url, json=app_data, auth=HTTPBasicAuth(username, password))

	# Print response for debugging
	print(response.status_code, response.text)
	time.sleep(1.0 + random.random())

#============================================
def main():
	"""
	Main function to fetch and send electricity pricing, solar data, and date info to AWTRIX.
	"""

	# Fetch solar energy data (current and total) and add them to the list
	current_data, total_data = solar_display.compile_solar_data()
	# Send solar data to AWTRIX
	send_to_awtrix(current_data)
	#send_to_awtrix(total_data)

	# Fetch the latest electricity price data and add to the list
	comed_data_dict = comed_price_display.compile_comed_price_data()
	send_to_awtrix(comed_data_dict)

	# Fetch formatted date data (e.g., "Sat Feb 22") and send to AWTRIX
	date_data = display_date.get_date_data()
	send_to_awtrix(date_data)

	comed_data_dict['name'] = 'SComed2'
	send_to_awtrix(comed_data_dict)

	# Introduce a small delay to avoid overwhelming the AWTRIX API
	time.sleep(1.0 + random.random())

	# Retrieve and log currently active apps on AWTRIX for debugging
	get_active_awtrix_apps()

#============================================
if __name__ == '__main__':
	main()
