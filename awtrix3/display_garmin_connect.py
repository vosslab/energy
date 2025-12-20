#!/usr/bin/env python3

import os
import time
import random
import datetime
import yaml
from garminconnect import Garmin  # PIP3 module

#============================================
def load_credentials(filename: str = "garmin_login.yml") -> dict:
	"""
	Load Garmin login credentials from a YAML file.

	Args:
		filename (str): Path to the YAML file.

	Returns:
		dict: Dictionary containing 'email' and 'password'.
	"""
	if not os.path.exists(filename):
		raise FileNotFoundError(f"Missing credentials file: {filename}")

	with open(filename, "r") as file:
		credentials = yaml.safe_load(file)

	if "email" not in credentials or "password" not in credentials:
		raise KeyError("Invalid format in garmin_login.yml. Ensure it has 'email' and 'password'.")

	return credentials

# Load Garmin Login Credentials from YAML file
credentials = load_credentials()
email = credentials["email"]
password = credentials["password"]

#============================================
# Global Variables
# Cache keeps per-day activity lists to reduce repeated API calls.
activity_cache = {}
# Reuse a logged-in client across calls to avoid re-auth churn.
client = None

#============================================
def connect_client() -> Garmin:
	"""
	Authenticate with Garmin Connect and return the client instance.
	Uses a global variable to avoid repeated logins.

	Returns:
		Garmin: Authenticated Garmin client instance.
	"""
	global client

	if client is None:
		client = Garmin(email, password)
		client.login()

	return client

#============================================
def get_activity_distance(start_date: datetime.date, end_date: datetime.date) -> float:
	"""
	Fetch total activity distance between two dates.

	Args:
		start_date (datetime.date): Start date for fetching activities.
		end_date (datetime.date): End date for fetching activities.

	Returns:
		float: Total distance in miles.
	"""
	client = connect_client()  # Ensure client is connected
	total_distance_meters = 0
	current_date = start_date

	while current_date <= end_date:
		date_str = current_date.isoformat()  # Convert date to string for cache key

		# Check if activities are already cached
		if date_str in activity_cache:
			daily_activities = activity_cache[date_str]
		else:
			try:
				time.sleep(random.random())  # Prevent rate limiting
				activities = client.get_activities_by_date(startdate=date_str, enddate=date_str)

				# Extract distance from each activity
				daily_activities = [act.get("distance", 0) for act in activities]

				# Store result in cache
				activity_cache[date_str] = daily_activities
			except KeyError:
				print(f"Data missing for {current_date}")
				daily_activities = []  # Default to empty if there's an error

		total_distance_meters += sum(daily_activities)  # Sum up activity distances
		current_date += datetime.timedelta(days=1)  # Move to next day

	# Convert meters to miles
	total_distance_miles = total_distance_meters / 1609.34
	return total_distance_miles

#============================================
def get_weekly_distance() -> float:
	"""
	Get total activity distance for the current week (from Monday).

	Returns:
		float: Weekly distance in miles.
	"""
	today = datetime.date.today()
	start_of_week = today - datetime.timedelta(days=today.weekday())  # Monday of this week
	return get_activity_distance(start_of_week, today)

#============================================
def get_monthly_distance() -> float:
	"""
	Get total activity distance for the current month.

	Returns:
		float: Monthly distance in miles.
	"""
	today = datetime.date.today()
	start_of_month = today.replace(day=1)  # First day of this month
	return get_activity_distance(start_of_month, today)

#============================================
def get_annual_distance() -> float:
	"""
	Get total activity distance for the current year.

	Returns:
		float: Annual distance in miles.
	"""
	today = datetime.date.today()
	start_of_year = today.replace(month=1, day=1)  # First day of this year
	return get_activity_distance(start_of_year, today)

#============================================
def logout():
	"""
	Log out from Garmin Connect and remove authentication tokens.
	"""
	global client
	if client:
		client.logout()
		client = None  # Reset client instance
		print("Logged out from Garmin.")

	# Delete stored authentication token only if needed
	token_file = os.path.expanduser("~/.garminconnect")
	if os.path.exists(token_file):
		os.remove(token_file)
		print("Token deleted. Next login will require authentication.")

#============================================
def main():
	"""
	Main function to fetch and display weekly and monthly distances.
	"""
	weekly_distance = get_weekly_distance()
	#monthly_distance = get_monthly_distance()
	# annual_distance = get_annual_distance()

	print(f"Weekly Distance: {weekly_distance:.2f} mi")
	#print(f"Monthly Distance: {monthly_distance:.2f} mi")
	# print(f"Annual Distance: {annual_distance:.2f} mi")


#============================================
if __name__ == "__main__":
	main()
