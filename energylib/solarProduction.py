#!/usr/bin/env python3

import sys
import time
import json
import ephem
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
			return None
		except requests.exceptions.ConnectionError:
			return None
	if fails >= 9:
		print("ERROR: too many failed requests")
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
	if isDaytime() is True:
		data = getSolarData()
	else:
		data = {}
	returnList = {}
	defvalue = { 'Value': 0, 'Unit': 'W', }
	for key in dataMap:
		returnList[dataMap[key]] = data.get(key, defvalue)
	return returnList

#======================================
def isDaytime(msg=False):
	somewhere = ephem.Observer()
	somewhere.lat = '42.12364'
	somewhere.lon = '-87.96472'
	somewhere.elevation = 205

	sun = ephem.Sun()
	sunrise = somewhere.next_rising(sun)
	sunset = somewhere.next_setting(sun)

	if msg is True:
		print(("Visual sunrise %s" % sunrise))
		print(("Visual sunset %s" % sunset))
	if sunrise < sunset:
		if msg: print("dark, sunrise before sunset")
		return False
	else:
		if msg: print("light, sunset before sunrise")
		return True

#======================================
#======================================
if __name__ == '__main__':
	isDaytime(msg=True)
	data = getSolarUsage()
	#print(data.keys())
	import pprint
	pprint.pprint(data)

	for key in data:
		print(("%s: %.2f k%s"%(key, int(data[key]['Value'])/1000., data[key].get('Unit',0))))
	print('\n')
