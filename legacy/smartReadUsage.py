#!/usr/bin/env python

import time
import numpy
#print(sys.path)

from legacy import readSMBus
from energylib import solarProduction

### all units in milliwatts (mW)
debug = True

#======================================
#======================================
def getSolarWatts():
	solardata = solarProduction.getSolarUsage()
	solarValue = float(solardata['Current Production']['Value'])
	#convert from watts to milliwatts
	solarwatts = int(solarValue*1000)
	return solarwatts

#======================================
#======================================
def getUsageWattsArray():
	return numpy.array(getUsageWattsList(), dtype=numpy.uint32)

#======================================
#======================================
def getUsageWattsList():
	return readSMBus.getUsageList()

#======================================
#======================================
def calculateEasySum(usageList):
	usageArray = numpy.array(usageList, dtype=numpy.uint32)
	if debug: print(usageArray)
	medianUsages = numpy.median(usageArray, axis=0)
	if debug: print(medianUsages)
	totalUsage = numpy.sum(medianUsages)
	return medianUsages, totalUsage

#======================================
#======================================
def smartReadSmbus(numReads=3, readDelay=15):
	usageList = []
	solarList = []
	for i in range(numReads):
		usageWatts = getUsageWattsList()
		usageList.append(usageWatts)
		solarWatts = getSolarWatts()
		solarList.append(solarWatts)
		if debug is True:
			outputstring = "solar: %d W, "%(solarWatts/1e3)
			for i, u in enumerate(usageWatts):
				outputstring += "c%d: %d W, "%(i, u/1e3)
			print(outputstring)
		time.sleep(readDelay)
	if numpy.sum(solarList) == 0:
		### easy case no solar
		return 0, calculateEasySum(usageList)
	return None

#======================================
#======================================
def fastReadSmbus():
	solar = getSolarWatts()
	usageList = getUsageWattsList()
	if solar == 0:
		totalUsage = numpy.sum(usageList)
		return "%.3f kW"%(totalUsage/1e6)
	numChannels = len(usageList)
	channelCount = 0
	for usage in usageList:
		if usage > 1.1*solar/float(numChannels):
			channelCount += 1
	if channelCount == numChannels:
		totalUsage = numpy.sum(usageList)
		return "%.3f kW"%(totalUsage/1e6)
	#not sure what to do?
	returnString = ""
	for usage in usageList:
		returnString += "&pm;%.2f kW"%(usage/1e6)
		returnString += " and "
	returnString[-5:] == ""
	return returnString

if __name__ == '__main__':
	print((fastReadSmbus()))
	print((smartReadSmbus(4, 4)))
