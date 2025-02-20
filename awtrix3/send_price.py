#!/usr/bin/env python3

# Standard Library

#pypi libraries
import yaml
import requests
from requests.auth import HTTPBasicAuth

# Local Repo Modules
#import solar_sun
import comed_price

#============================================
def send_to_awtrix(data_dict: dict):
	"""
	Sends the data to AWTRIX 3 display.
	"""
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
def main():
	"""
	Main function to fetch the latest electricity price and send it to AWTRIX.
	"""
	comed_data_dict = comed_price.compile_comed_price_data()
	send_to_awtrix(comed_data_dict)

#============================================
if __name__ == '__main__':
	main()
