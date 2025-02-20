
# Standard Library
import time

#pypi libraries
import numpy
import colorsys

# Local Repo Modules
import icon_draw
import sun_location
import solarProduction


#============================================
def get_current_production() -> float:
	"""
	Gets the current electricity price from ComEd API.

	Returns:
		float: Current price in cents.
	"""
	data = solarProduction.getSolarUsage()
	current_num = data["Current Production"].get('Value', 0)
	total_num = data["Today's Production"].get('Value', 0)
	for key in data:
		num = data[key].get('Value', 0)/1000.
		print(f"{key}: {num:.3f} kW")
	return current_num, total_num

#============================================
def compile_solar_data():
	"""
	Compile the electricity price to a data dict

	Args:
		price (float): The electricity price in cents.
	"""
	if not sun_location.is_the_sun_up_now():
		return None

	current_num, total_num = get_current_production()

	# Get to percentage daylight
	progress_value = sun_location.percent_of_daylight_complete()

	if current_num > 1000:
		text1 = f"{current_num/1000.:.1f} kW"
	else:
		text1 = f"{current_num:.0f} W"

	data1 = {
		"name": "SolarProduction",
		"text": text1,
		"icon": icon_draw.awtrix_icons['solar energy'],
		#"color": awtrix_color,  # Dynamic RGB color
		"progress": progress_value,  # Progress bar (minutes past the hour)
		"repeat": 10,
		"center": True,  # Disable text centering
		"duration": 5,
	}

	data2 = {
		"name": "SolarProduction",
		"text": f"{total_num/1000.:.1f} kWh",
		"icon": icon_draw.awtrix_icons['sunny'],
		#"color": awtrix_color,  # Dynamic RGB color
		"progress": progress_value,  # Progress bar (minutes past the hour)
		"repeat": 10,
		"center": True,  # Disable text centering
		"duration": 5,
	}

	return data1, data2

#============================================
def main():
	"""
	Main function to fetch the latest electricity price and send it to AWTRIX.
	"""
	data1, data2 = compile_solar_data()
	print(data1)
	print(data2)

#============================================
if __name__ == '__main__':
	main()
