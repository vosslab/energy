#!/usr/bin/env python3

# Traceback manager for CGI scripts
import cgitb
cgitb.enable()

import sys
import time
sys.path.append('/home/pi/energy')

# Lazy loading: import libraries only when needed
from energylib import comedlib, htmltools, smartReadUsage, solarProduction, ecobeelib

# Content-Type header
print("Content-Type: text/html\n")
print("<head><title>House Energy Usage</title></head>")
print("<body>")
print(f"<h1>House Energy Usage</h1><h3>Current time:</h3>{time.asctime()}<br/>\n")
print("<a href='comed.py'>Show Only Comed Prices</a><br/>")
print("<a href='fullhouse.py'>Show Full House Display with Graphs</a><br/>")

# Function to record the time taken for each block
def measure_time(start_time):
    return time.time() - start_time

# Block 1: Fetch solar data
start_time = time.time()
try:
    solardata = solarProduction.getSolarUsage()
    solar_data_html = "<h3>Solar Data</h3>" + "".join(
        f"{key}: {int(solardata[key]['Value'])/1000.:.3f} k{solardata[key]['Unit']}<br/>"
        for key in solardata if int(solardata[key]['Value']) > 0
    )
    print(solar_data_html)
except Exception as e:
    print("<h3>Solar Data</h3>Failed to load solar data<br/>")
    print(f"Error: {str(e)}<br/>")
print(f"<small>Solar data load time: {measure_time(start_time):.2f} seconds</small><br/>")

# Block 2: Fetch energy usage
start_time = time.time()
try:
    usageText = smartReadUsage.fastReadSmbus()
    print(f"<h3>Energy Usage</h3><span style='color: #880000'>Current Usage: {usageText}</span><br/>")
except Exception as e:
    print("<h3>Energy Usage</h3>Failed to read energy usage<br/>")
    print(f"Error: {str(e)}<br/>")
print(f"<small>Energy usage load time: {measure_time(start_time):.2f} seconds</small><br/>")

# Block 3: Fetch Ecobee data
start_time = time.time()
try:
    print(htmltools.htmlEcobee())
except Exception as e:
    print('<br/>ECOBEE failed to load, tell Neil<br/>')
    print(f"Error: {str(e)}<br/>")
print(f"<small>Ecobee data load time: {measure_time(start_time):.2f} seconds</small><br/>")

# Block 4: Fetch Comed data
start_time = time.time()
try:
    print(htmltools.htmlComedData())
except Exception as e:
    print('<br/>COMED data failed to load<br/>')
    print(f"Error: {str(e)}<br/>")
print(f"<small>Comed data load time: {measure_time(start_time):.2f} seconds</small><br/>")

# Footer
print('<br/>\n<br/>\n</body></html>')
