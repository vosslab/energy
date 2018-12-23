#!/usr/bin/env python

# Distributed with a free-will license.
# Use it any way you want, profit or free, provided it fits in the licenses of its associated works.
# This code is designed to work with the PECMAC125A_DLCT03C20 I2C Mini Module available from ControlEverything.com.
# https://www.controleverything.com/content/Current?sku=PECMAC125A_DLCT03C20#tabs-0-product_tabset-2

import time
import smbus

# Get I2C bus
bus = smbus.SMBus(1)
noOfChannel = 2

command1 = [0x6A, 0x01, 0x01, 0x0C, 0x00, 0x00, 0x0A]
bus.write_i2c_block_data(0x2A, 0x92, command1)

time.sleep(0.5)

data1 = bus.read_i2c_block_data(0x2A, 0x55, noOfChannel*3 + 3)

# Convert the data
totalCurrent = 0
currents = []
for i in range(0, noOfChannel) :
	msb1 = data1[i * 3]
	msb = data1[1 + i * 3]
	lsb = data1[2 + i * 3]

	# Convert the data to ampere
	current = (msb1 * 65536 + msb * 256 + lsb) / 1000.0

	# Output data to screen
	#print "Channel no : %d " %(i+1)
	#print "  Current : %.2f A"%(current)
	#print "  Usage   : %.2f kW"%(current*0.12)
	currents.append(current)
	totalCurrent += current

#print "TOTAL"
#print "  Current : %.2f A"%(totalCurrent)
#print "  Usage   : %.2f kW"%(totalCurrent*0.120)

datestamp = time.strftime("%Y-%m%b-%d-%a").lower()
logname = "usage/%s.log"%(datestamp)
print("Usage: %.2f kW --> %s"%(totalCurrent*0.120, logname))

f = open(logname, "a")
f.write("%d,%.4f,%.4f,%.4f\n"%
	(time.time(), totalCurrent,
	currents[0], currents[1]))
f.close()
