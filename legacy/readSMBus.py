#!/usr/bin/env python3

import time
import smbus

# Distributed with a free-will license.
# Use it any way you want, profit or free,
#   provided it fits in the licenses of its associated works.
# This code is designed to work with the PECMAC125A_DLCT03C20 I2C Mini Module
#   available from ControlEverything.com.
# https://www.controleverything.com/content/Current?sku=PECMAC125A_DLCT03C20

#======================================
#======================================
def getUsageList():
	"""
	return list of usages in milliwatts
	"""

	numberOfChannels = 2

	# Get I2C bus
	bus = smbus.SMBus(1)

	# PECMAC125A address, 0x2A(42)
	# Command for reading current
	# 0x6A(106), 0x01(1), 0x01(1),0x0C(12), 0x00(0), 0x00(0) 0x0A(10)
	# Header byte-2, command-1, start channel-1, stop channel-12, byte 5 and 6 reserved, checksum
	command1 = [0x6A, 0x01, 0x01, 0x0C, 0x00, 0x00, 0x0A]
	bus.write_i2c_block_data(0x2A, 0x92, command1)

	time.sleep(0.01)

	# PECMAC125A address, 0x2A(42)
	# Read data back from 0x55(85), No. of Channels * 3 bytes
	# current MSB1, current MSB, current LSB
	data1 = bus.read_i2c_block_data(0x2A, 0x55, numberOfChannels*3 + 3)

	# Convert the data
	usageList = []
	for i in range(numberOfChannels):
		msb1 = data1[i*3]
		msb = data1[1 + i*3]
		lsb = data1[2 + i*3]

		# Convert the data to milliamperes
		current = (msb1 * 65536 + msb * 256 + lsb)
		# Convert the data to milliwatts
		usage = current * 120 #120V

		usageList.append(usage)
	return usageList


if __name__ == '__main__':
	usageList = getUsageList()
	print(usageList)
