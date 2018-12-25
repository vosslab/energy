#!/usr/bin/env python

import os
import sys
import time
import json
import ephem
import random
import requests
import datetime

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
	now = somewhere.date


	sun = ephem.Sun()
	r1 = somewhere.next_rising(sun)
	s1 = somewhere.next_setting(sun)

	somewhere.horizon = '-0:34'
	r2 = somewhere.next_rising(sun)
	s2 = somewhere.next_setting(sun)
	if msg is True:
		print ("Local time %s" % now)
		print ("Visual sunrise %s" % r1)
		print ("Visual sunset %s" % s1)
		print ("Naval obs sunrise %s" % r2)
		print ("Naval obs sunset %s" % s2)
	if now < s1:
		if msg: print "dark, before sunrise"
		return False
	elif now > s2:
		if msg: print "dark, after sunset"
		return False
	else:
		if msg: print "light"
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
		print("%s: %.2f k%s"%(key, int(data[key]['Value'])/1000., data[key].get('Unit',0)))
	print('\n')
