
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
	kw_num = None
	for key in data:
		kw_num = data[key].get('Value', 0)/1000.
		print(f"{kw_num} kW")
	return kw_num

#============================================
def compile_solar_data():
	"""
	Compile the electricity price to a data dict

	Args:
		price (float): The electricity price in cents.
	"""
	if not sun_location.is_the_sun_up_now():
		return None

	kw_num = get_current_production()

	# Get to percentage daylight
	progress_value = sun_location.percent_of_daylight_complete()

	data = {
		"name": "SolarProduction",
		"text": f"{kw_num:.1f} kW",
		"icon": icon_draw.awtrix_icons['sunny'],
		#"color": awtrix_color,  # Dynamic RGB color
		"progress": progress_value,  # Progress bar (minutes past the hour)
		"repeat": 10,
		"center": False,  # Disable text centering
	}

	return data

#============================================
def main():
	"""
	Main function to fetch the latest electricity price and send it to AWTRIX.
	"""
	comed_data_dict = compile_comed_price_data()
	print(comed_data_dict)

#============================================
if __name__ == '__main__':
	main()
