#!/usr/bin/env python3

import sys
import time
import cgitb
from energylib import comedlib
from energylib import htmltools

# Enable traceback debugging for CGI
cgitb.enable()

def generate_html() -> str:
	"""
	Generates the Comed Hourly Prices HTML page as a string.
	Returns:
		str: The full HTML page content.
	"""
	return """<!DOCTYPE html>
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

if __name__ == '__main__':
	# Always print to standard output (for CGI)
	print("Content-Type: text/html\n")
	print(generate_html())
