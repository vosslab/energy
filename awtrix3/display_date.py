from datetime import datetime


def get_date_data():
	"""
	Creates an AWTRIX 3 data packet to display the current date with:
	- "Sa Feb" in white text
	- "22" in black text with a white background box
	"""

	# Get the current date information
	now = datetime.now()
	weekday_name = now.strftime("%A")  # Full weekday name (e.g., "Saturday")
	weekday = weekday_name[:2]  # Short weekday name for display (e.g., "Sa")
	month_name = now.strftime("%B")   # Full month name (e.g., "February")
	month = now.strftime("%b")        # Short month name (e.g., "Feb")
	day = now.strftime("%d")          # Numeric day (e.g., "22")

	# Subtle palette for weekday/month text on the 32x8 display.
	day_colors = {
		"Monday": "#8000ff",  # Bright purple-violet
		"Tuesday": "#ff0000",  # Vivid warm red
		"Wednesday": "#ffd500",  # Bright warm yellow
		"Thursday": "#FF8800",  # Bold orange
		"Friday": "#00ff4c",  # Vibrant green
		"Saturday": "#0040ff",  # Vivid blue
		"Sunday": "#ffbf00",  # Rich gold-yellow
	}
	month_colors = {
		"January": "#3399ff",  # Brighter cold blue
		"February": "#ff4733",  # Brighter scarlet red-orange
		"March": "#80ff80",  # Shamrock green
		"April": "#bf66ff",  # Pastel lavender
		"May": "#ffdd33",  # Golden yellow
		"June": "#ff4da6",  # Brighter deep magenta
		"July": "#33ff33",  # Vibrant green
		"August": "#ff7733",  # Brighter fiery red-orange
		"September": "#1ab2ff",  # Brighter sky blue
		"October": "#ff8000",  # Brighter pumpkin orange
		"November": "#8533ff",  # Vivid purple
		"December": "#00cc00",  # Bright green
	}

	def _char_width(ch: str) -> int:
		if ch in {"M", "W", "m", "w"}:
			return 5
		if ch == " ":
			return 1
		return 3

	def _text_width(text: str, letter_gap: int = 1) -> int:
		if not text:
			return 0
		width = 0
		for i, ch in enumerate(text):
			width += _char_width(ch)
			if i < len(text) - 1:
				width += letter_gap
		return width

	# Prefer a visible space between weekday and month, except for known tight combos.
	use_space = True
	if weekday in {"Mo", "We"} and month in {"Mar", "May"}:
		use_space = False

	box_width = 9
	available_width = 32 - box_width
	full_text = f"{weekday}{' ' if use_space else ''}{month}"
	if _text_width(full_text) > available_width:
		use_space = False

	prefix = f"{weekday}{' ' if use_space else ''}"
	month_x = _text_width(prefix)

	# Define the white box behind the day number (positioned manually).
	# x=10, y=0, width=8, height=7, color=white
	white_outline = {"df": [32-box_width, 0, box_width, 8, "#eeeeee"]}
	number_date = {"dt": [32-box_width+1, 2, f"{day}", "#111111"]}
	weekday_draw = {"dt": [0, 2, f"{weekday}", day_colors.get(weekday_name, "#dddddd")]}
	month_draw = {"dt": [month_x, 2, f"{month}", month_colors.get(month_name, "#dddddd")]}
	red_header = {"df": [32-box_width, 0, box_width, 2, "#B22222"]}

	# Construct the AWTRIX data dictionary.
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
		# Draw commands render in-order on the 32x8 canvas.
		"draw": [white_outline, weekday_draw, month_draw, number_date, red_header]
	}

	return date_display
