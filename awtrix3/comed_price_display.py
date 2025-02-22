
# Standard Library
import time

#pypi libraries
import numpy
import colorsys

# Local Repo Modules
import icon_draw
import comedlib

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
def icon_price_awtrix(price: float) -> int:
	if price < 0:
		return icon_draw.awtrix_icons['download blue']
	elif price < 3:
		return icon_draw.awtrix_icons['green power plug']
	elif price < 5:
		return icon_draw.awtrix_icons['yellow power plug']
	elif price < 7:
		return icon_draw.awtrix_icons['orange power plug']
	elif price < 10:
		return icon_draw.awtrix_icons['red power plug']
	return icon_draw.awtrix_icons['red x']

#============================================
def arrow_price_awtrix(trend: str) -> list:
	if trend == "up":
		up_arrow = icon_draw.draw_arrow(29, "up", "#B24444")
		return up_arrow
	elif trend == "down":
		down_arrow = icon_draw.draw_arrow(29, "down", "#448B44")
		return down_arrow
	mid_arrow = icon_draw.draw_arrow(29, "mid", "#888888")
	return mid_arrow


#============================================
def get_current_price() -> float:
	"""
	Gets the current electricity price from ComEd API.

	Returns:
		float: Current price in cents.
	"""
	comed = comedlib.ComedLib()
	price = comed.getCurrentComedRate()
	print(f"Current Power Price: {price:.2f}¢")
	recent = comed.getMostRecentRate()
	print(f"Recent  Power Price: {recent:.1f}¢")
	if recent < price - 0.2:
		trend = "down"
	elif recent > price + 0.2:
		trend = "up"
	else:
		trend = "none"
	print(f"Trend: {trend}")
	return price, trend

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

	# Determine icon (based on pricing level)
	icon_id = icon_price_awtrix(price)

	# Determine arrow (based on pricing trend)
	arrow = arrow_price_awtrix(trend)

	data = {
		"name": "ComedPrice",
		"text": f"{price:.1f}¢",
		"icon": icon_id,
		"color": awtrix_color,  # Dynamic RGB color
		"progress": progress_value,  # Progress bar (minutes past the hour)
		"progressC": awtrix_color,
		"repeat": 20,
		"draw": arrow,
		"center": False,  # Disable text centering
		"duration": 15,
		"stack": True,
		"lifetime": 120,
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
