#!/usr/bin/env python3

import time
from comed import generate_html

OUTPUT_FILE = "/var/www/html/comed.html"

def generate_static_page():
	"""
	Generates and writes the static Comed HTML file.
	"""
	html_content = generate_html()
	with open(OUTPUT_FILE, "w") as f:
		f.write(html_content)
	print(f"Generated {OUTPUT_FILE} at {time.asctime()}")

if __name__ == '__main__':
	generate_static_page()
