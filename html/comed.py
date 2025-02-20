#!/usr/bin/env python3

import sys
import time
import cgitb
import numpy
from energylib import comedlib
from energylib import htmltools

# Enable traceback debugging for CGI
cgitb.enable()

sys.path.append('/home/pi/energy')

def generate_html(output_file=None):
	"""
	Generates the Comed Hourly Prices HTML page.
	If `output_file` is specified, writes the output to a file instead of printing.
	"""
	html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Comed Hourly Prices</title>
</head>
<body>
    <h1>Comed Hourly Prices</h1>
    <a href='house.py'>Show All Energy Data</a><br/>
    <h3>Current time:</h3> {current_time}
    <br/>
    {comed_data}
</body>
</html>""".format(
		current_time=time.asctime(),
		comed_data=htmltools.htmlComedData()
	)

	# If an output file is provided, write to it
	if output_file:
		with open(output_file, "w") as f:
			f.write(html_content)
	else:
		# CGI mode - print to standard output
		print("Content-Type: text/html\n")
		print(html_content)

if __name__ == '__main__':
	# If called directly, generate a static file instead of CGI output
	generate_html("/var/www/html/comed.html")  # Adjust the path as needed
