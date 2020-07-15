#Traceback manager for CGI scripts
import cgitb
cgitb.enable()

import time
import numpy
from energylib import comedlib
from energylib import htmltools

print("Content-Type: text/html\n")
print("\n")
print("<head>")
print("<title>Comed Hourly Prices</title>")
print("</head>")

#======================================
print("<body>")
print("<h1>Comed Hourly Prices</h1>")
print("<a href='house.py'>Show All Energy Data</a><br/>")
print("<h3>Current time:</h3>%s"%(time.asctime()))
print('<br/>\n')

#======================================
#======================================
print(htmltools.htmlComedData())


#======================================
#======================================
print("</body></html>")
