#!/usr/bin/env python

import os
import sys
import time
import json
import random
import requests

inverter_ip = "192.168.2.188"

#======================================
def safeDownloadWebpage(url):
	fails = 0
	while(fails < 9):
		try:
			resp = requests.get(url, timeout=1)
			break
		except requests.exceptions.ReadTimeout:
			#print "FAILED request"
			fails+=1
			time.sleep(random.random()+ fails**2)
			continue
		except requests.exceptions.ConnectTimeout:
			#print "FAILED connect"
			return None
			fails+=2
			time.sleep(random.random()+ fails**2)
			continue
	if fails >= 9:
		print "ERROR: too many failed requests"
		sys.exit(1)
	return resp

#======================================
dataMap = {
	'PAC': 'Current Production',
	'DAY_ENERGY': "Today's Production",
}

#======================================
def getSolarData():
	params = "Scope=Device&DeviceId=1&DataCollection=CommonInverterData"
	inverter_url = "http://%s/solar_api/v1/GetInverterRealtimeData.cgi?%s"%(inverter_ip, params)
	resp = safeDownloadWebpage(inverter_url)
	if resp is None:
		return {}
	#print dir(resp)
	bulktables = json.loads(resp.text)
	data = dict(bulktables['Body']['Data'])
	return data

#======================================
def getSolarUsage():
	data = getSolarData()
	returnList = {}
	defvalue = { 'Value': 0, 'Unit': 'W', }
	for key in dataMap:
		returnList[dataMap[key]] = data.get(key, defvalue)
	return returnList

#======================================
#======================================
if __name__ == '__main__':
	data = getSolarData()
	#print(data.keys())
	import pprint
	#pprint.pprint(data)
	
	for key in dataMap:
		print("%s: %.2f k%s"%(dataMap[key], int(data[key]['Value'])/1000., data[key].get('Unit',0)))
	print('\n')
	