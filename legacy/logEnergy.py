#!/usr/bin/env python3

# Distributed with a free-will license.
# Use it any way you want, profit or free, provided it fits in the licenses of its associated works.
# This code is designed to work with the PECMAC125A_DLCT03C20 I2C Mini Module available from ControlEverything.com.
# https://www.controleverything.com/content/Current?sku=PECMAC125A_DLCT03C20#tabs-0-product_tabset-2

import time
import smbus
from energylib import solarProduction

def getCurrent():
	# Get I2C bus
	bus = smbus.SMBus(1)
	noOfChannel = 2
	command1 = [0x6A, 0x01, 0x01, 0x0C, 0x00, 0x00, 0x0A]
	bus.write_i2c_block_data(0x2A, 0x92, command1)
	time.sleep(0.1)
	data1 = bus.read_i2c_block_data(0x2A, 0x55, noOfChannel*3 + 3)
	# Convert the data
	totalCurrent = 0
	currents = []
	for i in range(0, noOfChannel) :
		msb1 = data1[i*3]
		msb = data1[1 + i*3]
		lsb = data1[2 + i*3]
		# Convert the data to milliamperes
		current = (msb1 * 65536 + msb * 256 + lsb)
		if current > 8000000:
			current = 0
		currents.append(current)
		totalCurrent += current
	return currents, totalCurrent

def getSolarCurrent():
	solardata = solarProduction.getSolarUsage()
	solarValue = float(solardata['Current Production']['Value'])
	#convert from watts to milliamps
	solarcurrent = int(round(solarValue/0.12))
	return solarcurrent


readDelay = 15
currents1, totalCurrent1 = getCurrent()
solarcurrent1 = getSolarCurrent()
print(("Usage 1/3: %.1f W use / %.1f W solar"
	%(totalCurrent1*120/1e3, solarcurrent1*120/1e3)))
time.sleep(readDelay)
currents2, totalCurrent2 = getCurrent()
solarcurrent2 = getSolarCurrent()
print(("Usage 2/3: %.1f W use / %.1f W solar"
	%(totalCurrent2*120/1e3, solarcurrent2*120/1e3)))
time.sleep(readDelay)
currents3, totalCurrent3 = getCurrent()
solarcurrent3 = getSolarCurrent()
print(("Usage 3/3: %.1f W use / %.1f W solar"
	%(totalCurrent3*120/1e3, solarcurrent3*120/1e3)))

#take the median values
solarcurrent = sorted([solarcurrent1, solarcurrent2, solarcurrent3])[1]
totalCurrent = sorted([totalCurrent1, totalCurrent2, totalCurrent3])[1]
currents = []
for i in range(len(currents1)):
	current = sorted([currents1[i], currents2[i], currents3[i]])[1]
	currents.append(current)

datestamp = time.strftime("%Y-%m%b-%d-%a").lower()
logname = "usage/%s.log"%(datestamp)
print(("Usage Avg: %.3f kW use / %.3f kW solar --> %s"%(totalCurrent*120/1e6, solarcurrent*120/1e6, logname)))

f = open(logname, "a")
f.write("%d,%d,%d,%d,%d\n"%
	(time.time(), totalCurrent,
	currents[0], currents[1], solarcurrent))
f.close()
