
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
		print("Sun is set, no more solar until sunrise")
		return None, None

	current_num, total_num = get_current_production()
	#if total_num == 0 or current_num == 0:
	#	return None, None

	# Get to percentage daylight
	progress_value = sun_location.percent_of_daylight_complete()

	if current_num > 1000:
		current_text1 = f"{current_num/1000.:.1f} kW"
	else:
		current_text1 = f"{current_num:.0f} W"

	current_data = {
		"name": "CurrentSolar",
		"text": current_text1,
		"icon": icon_draw.awtrix_icons['solar energy'],
		#"color": awtrix_color,  # Dynamic RGB color
		"progress": progress_value,  # Progress bar (minutes past the hour)
		"repeat": 20,
		"center": True,
		"duration": 5,
		"stack": True,
		"lifetime": 120,
	}

	total_data = {
		"name": "TotalSolar",
		"text": f"{total_num/1000.:.1f} kWh",
		"textCase": 2,
		#"icon": icon_draw.awtrix_icons['sunny'],
		"icon": icon_draw.awtrix_icons['solar energy'],
		#"color": awtrix_color,  # Dynamic RGB color
		"progress": progress_value,  # Progress bar (minutes past the hour)
		"repeat": 20,
		"center": False,
		"noScroll": True,
		"scrollSpeed": 1,
		"duration": 5,
		"stack": True,
		"lifetime": 120,
	}

	return current_data, total_data

#============================================
def main():
	"""
	Main function to fetch the latest electricity price and send it to AWTRIX.
	"""
	current_data, total_data = compile_solar_data()
	print(current_data)
	print(total_data)

#============================================
if __name__ == '__main__':
	main()
