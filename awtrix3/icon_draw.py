
# AWTRIX Icons Dictionary
awtrix_icons = {
	'power into plug': 40828,
	'STOP': 51783,
	'green box with check': 46832,
	'green check mark': 4474,
	'red x': 270,
	'lightning': 95,
	'green plus': 17093,
	'green arrow up': 120,
	'red arrow down': 124,
	'green arrow down': 402,
	'red arrow up': 4103,
	'solar panels': 53183,
	'sun with blue bg': 50,
	'sunny': 2282,
	'solar energy': 60102,
	}


#============================================
def draw_arrow(center_x: int, direction: str, color: str=None):
	"""
	Generates drawing instructions for an up or down arrow with a given center pixel.

	Args:
		center_x (int): X position of the center pixel.
		center_y (int): Y position of the center pixel.
		direction (str): "up" or "down" to determine arrow orientation.
		color (str): Color of the arrow in hex format (e.g., "#FF0000").

	Returns:
		list: List of AWTRIX draw commands.
	"""
	if direction == "up":
		#color = up_color if color is None
		arrow_list = [
			{"dl": [center_x, 0, center_x,      5, color]},  # Shaft (1 pixel wide)
			{"dl": [center_x, 0, center_x - 2,  2, color]},  # Left tip
			{"dl": [center_x, 0, center_x + 2,  2, color]}   # Right tip
		]
	elif direction == "down":
		arrow_list = [
			{"dl": [center_x, 0, center_x,      5, color]},  # Shaft (1 pixel wide)
			{"dl": [center_x, 5, center_x - 2,  3, color]},  # Left tip
			{"dl": [center_x, 5, center_x + 2,  3, color]}   # Right tip
		]
	elif direction == "mid":
		arrow_list = [
			{"dl": [center_x-2, 3, center_x+2,  3, color]},  # Shaft (1 pixel wide)
			{"dl": [center_x-2, 3, center_x,    5, color]},  # Left tip
			{"dl": [center_x+2, 3, center_x,    1, color]}   # Right tip
		]
	else:
		raise ValueError("Direction must be 'up' or 'down'.")
	return arrow_list
