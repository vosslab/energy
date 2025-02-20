#!/usr/bin/env python3

import datetime
import math

def sine_wave(x: float, A: float, B: float, C: float, D: float) -> float:
	"""
	Sine wave function used to approximate sunrise and sunset times.
	Args:
		x (float): Day of the year (1-365)
		A, B, C, D (float): Parameters from curve fitting
	Returns:
		float: Approximate hour in decimal (e.g., 6.5 means 6:30 AM)
	"""
	return A * math.sin(B * (x - C)) + D

def decimal_to_hm(decimal_hour: float) -> str:
	"""
	Convert decimal hour (e.g., 6.5) to HH:MM format.
	Args:
		decimal_hour (float): Time in decimal format
	Returns:
		str: Formatted time string in HH:MM format
	"""
	hours = int(decimal_hour)
	minutes = int((decimal_hour - hours) * 60)
	return f"{hours:02}:{minutes:02}"

def get_sun_times(day_of_year: int) -> dict:
	"""
	Estimate sunrise and sunset times for Chicago using a sine wave model.
	Args:
		day_of_year (int): Day of the year (1 = Jan 1, 365 = Dec 31)
	Returns:
		dict: Sunrise and sunset times in HH:MM format
	"""
	# Fitted sine wave parameters for Chicago
	sunrise_params = [-1.52, 0.0162, 80.4, 5.86]  # Sunrise
	sunset_params = [1.59, 0.0162, 69.5, 17.87]   # Sunset

	# Compute sunrise and sunset
	sunrise = sine_wave(day_of_year, *sunrise_params)
	sunset = sine_wave(day_of_year, *sunset_params)

	# Format as HH:MM
	return {
		"sunrise": decimal_to_hm(sunrise),
		"sunset": decimal_to_hm(sunset),
		"sunrise_decimal": sunrise,
		"sunset_decimal": sunset
	}

def is_the_sun_up_now() -> bool:
	"""
	Determine whether the sun is currently up in Chicago.
	Returns:
		bool: True if the sun is up, False otherwise.
	"""
	# Get current time and convert to decimal hours
	now = datetime.datetime.now()
	current_time_decimal = now.hour + now.minute / 60

	# Get today's sunrise and sunset times
	day_of_year = now.timetuple().tm_yday
	sun_times = get_sun_times(day_of_year)

	# Check if the current time is between sunrise and sunset
	return sun_times["sunrise_decimal"] <= current_time_decimal <= sun_times["sunset_decimal"]

if __name__ == '__main__':
	# Get today's sunrise and sunset times
	day_of_year = datetime.date.today().timetuple().tm_yday
	sun_times = get_sun_times(day_of_year)

	# Print results
	print(f"Chicago Sunrise: {sun_times['sunrise']}, Sunset: {sun_times['sunset']}")
	print(f"Is the sun up now? {'Yes' if is_the_sun_up_now() else 'No'}")
