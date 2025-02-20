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
	#print(f"Sending data to {ip}")
	print(f"Sending {len(data_dict)} data packets to {ip}")
	url = f"http://{ip}/api/custom"
	try:
		print(f"  TEXT: '{data_dict.get('text', '')}'")
	except AttributeError:
		pass
	response = requests.post(url, json=data_dict, auth=HTTPBasicAuth(username, password))

	# Print response for debugging
	print(response.status_code, response.text)
	time.sleep(random.random())

#============================================
def main():
	"""
	Main function to fetch the latest electricity price and send it to AWTRIX.
	"""
	data_list = []
	current_data, total_data = solar_display.compile_solar_data()
	data_list += [current_data, total_data]
	#send_to_awtrix(current_data)
	#send_to_awtrix(total_data)
	comed_data_dict = comed_price_display.compile_comed_price_data()
	data_list.append(comed_data_dict)
	#send_to_awtrix(comed_data_dict)
	send_to_awtrix(data_list)

#============================================
if __name__ == '__main__':
	main()
