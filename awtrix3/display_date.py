from datetime import datetime


def get_date_data():
	"""
	Creates an AWTRIX 3 data packet to display the current date with:
	- "Sa Feb" in white text
	- "22" in black text with a white background box
	"""

	# Get the current date information
	now = datetime.now()
	weekday = now.strftime("%a")[:2]  # Short weekday name (e.g., "Sa")
	month = now.strftime("%b")        # Short month name (e.g., "Feb")
	day = now.strftime("%d")          # Numeric day (e.g., "22")

	# Define the white box behind the day number (positioned manually)
	box_width = 9
	# x=10, y=0, width=8, height=7, color=white
	white_outline = {"df": [32-box_width, 0, box_width, 8, "#eeeeee"]}
	number_date = {"dt": [32-box_width+1, 2, f"{day}", "#111111"]}
	day_month = {"dt": [0, 2, f"{weekday}{month}", "#dddddd"]}
	red_header = {"df": [32-box_width, 0, box_width, 2, "#B22222"]}

	# Construct the AWTRIX data dictionary
	date_display = {
		"name": "DateDisplay",
		#"text": f"{weekday}{month}",
		"textCase": 2,  # Keep mixed case (not all uppercase)
		"repeat": 20,   # Show for a longer duration
		"center": True,  # Center-align the text
		"duration": 5,   # Display for 5 seconds per cycle
		"stack": True,   # Ensure it stacks properly
		"noScroll": True,  # Prevent scrolling
		"lifetime": 300,  # Keep it active for 5 minutes
		"center": False,  # Disable text centering
		"draw": [white_outline, day_month, number_date, red_header]  # Add the white box to the drawing queue
	}

	return date_display

