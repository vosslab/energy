#!/usr/bin/env python3

# Standard Library
import os
import sys
import time
import math
import json
import random
import datetime
import shelve
# PIP modules
import numpy
import requests
from scipy import stats

#======================================
#======================================
class ComedLib(object):
	"""
	Class to interact with ComEd's pricing data. Handles downloading, caching, and parsing of data.
	"""

	def __init__(self):
		"""Initializes the ComedLib object, setting up cache settings and base URL."""
		self.useCache = True
		self.debug = False
		# Use a single shared cache file in /tmp
		self.cache_file = "/tmp/comed_cache_file.json"
		# Ensure the file exists and set permissions
		# Ensure the file exists and has correct permissions
		if not os.path.exists(self.cache_file):
			with open(self.cache_file, "w") as f:
				f.write("{}")  # Initialize empty JSON cache
			try:
				os.chmod(self.cache_file, 0o666)  # Allow all users to read/write
			except PermissionError:
				print(f"WARNING: Could not set permissions for {self.cache_file}")

		self.cache_expiry_seconds = 240  # Cache expiry time in seconds

		scriptdir = os.path.dirname(__file__)
		self.baseurl = "https://hourlypricing.comed.com/api?type=5minutefeed"
		self.parsed_data_cache = None  # In-memory cache for parsed data
		self.raw_data_cache = None  # In-memory cache for raw data

	#======================================
	def downloadComedJsonData(self, url=None):
		"""
		Downloads the ComEd JSON data. Uses in-memory cache if available and valid,
		otherwise attempts to read from persistent cache or download fresh data.

		Args:
			url (str, optional): URL to download the JSON data from. Defaults to None.

		Returns:
			list: JSON data as a list of dictionaries, or None if download or parsing fails.
		"""
		# Try to use in-memory cache first
		if self.raw_data_cache:
			data_age = time.time() - self.raw_data_cache['timestamp']
			if data_age < self.cache_expiry_seconds:
				if self.debug:
					print(f".. Using comed data from in-memory cache .. age {data_age:.1f} seconds")
				return self.raw_data_cache['data']
		self.parsed_data_cache = None

		# Try to read from persistent cache
		data = self.readCache()
		if data:
			if self.debug:
				print(".. Using comed data from persistent cache")
			self.raw_data_cache = {'data': data, 'timestamp': time.time()}  # Update in-memory cache
			return data

		# Download new data if cache is not available or expired
		if self.debug:
			print(".. Downloading new comed data")
		if url is None:
			url = self.getUrl()
		resp = self.safeDownloadWebpage(url)
		try:
			data = json.loads(resp.text)
		except ValueError:
			return None

		# Save data to cache
		self.writeCache(data)
		self.raw_data_cache = {'data': data, 'timestamp': time.time()}  # Update in-memory cache
		return data

	#======================================
	def parseComedData(self, data=None):
		"""
		Parses the ComEd data and caches the result for reuse.

		Args:
			data (list, optional): Raw JSON data as a list of dictionaries. Defaults to None.

		Returns:
			dict: Dictionary with hours as keys and lists of prices as values.
		"""
		if data is None:
			data = self.downloadComedJsonData()
		if self.parsed_data_cache is not None:
			return self.parsed_data_cache  # Use cached parsed data

		yvalues = {}
		day = None
		for p in data:
			ms = int(p['millisUTC'])
			price = float(p['price'])
			timestruct = list(time.localtime(ms / 1000.))
			if day is None:
				day = timestruct[2]

			hours = timestruct[3] + timestruct[4] / 60.
			#print(f"{hours:.2f}<br/>")
			if timestruct[2] != day:
				hours -= 24.
			hour = int(hours) + 1
			hour2 = float(hour) - 0.99
			if hour in yvalues:
				yvalues[hour].append(price)
				yvalues[hour2].append(price)
			else:
				yvalues[hour] = [price]
				yvalues[hour2] = [price]

		# Cache the parsed data for reuse
		self.parsed_data_cache = yvalues
		#print(f"{yvalues.keys()}<br/>")
		return yvalues

	#======================================
	def writeCache(self, data):
		"""
		Writes data to the persistent cache using JSON.
		"""
		if not self.useCache:
			return

		cache_data = {
			"data": data,
			"timestamp": int(time.time())
		}
		with open(self.cache_file, "w") as file:
			json.dump(cache_data, file)

		if self.debug:
			print(f".. Saved cache to {self.cache_file}")

	#======================================
	def readCache(self):
		"""
		Reads data from the persistent cache if available and valid.

		Returns:
			list: Cached JSON data as a list of dictionaries, or None if cache is invalid or not present.
		"""
		if not self.useCache:
			return None
		# Check if file exists
		if not os.path.exists(self.cache_file):
			return None
		with open(self.cache_file, "r") as file:
			cache_data = json.load(file)
		# Validate cache structure
		if "timestamp" not in cache_data or "data" not in cache_data:
			return None
		# Check if cache is expired
		if time.time() - cache_data["timestamp"] > self.cache_expiry_seconds:
			return None
		if self.debug:
			print(f".. Using cached data from {self.cache_file}")
		return cache_data["data"]

	#======================================
	def safeDownloadWebpage(self, url):
		"""
		Safely downloads a webpage with retry logic for handling network errors.

		Args:
			url (str): URL to download.

		Returns:
			requests.Response: HTTP response object.

		Exits:
			Exits the program if too many failures occur during download.
		"""
		fails = 0
		verify = True
		while(fails < 9):
			try:
				resp = requests.get(url, timeout=1, verify=verify)
				break
			except requests.exceptions.ReadTimeout:
				fails += 1
				time.sleep(random.random() + fails**2)
				continue
			except requests.exceptions.ConnectTimeout:
				fails += 2
				time.sleep(random.random() + fails**2)
				continue
			except requests.exceptions.SSLError:
				fails += 1
				verify = False
		if fails >= 9:
			print("ERROR: too many failed requests")
			sys.exit(1)
		return resp

	#======================================
	def getUrl(self):
		"""
		Returns the base URL for downloading data.

		Returns:
			str: Base URL for data.
		"""
		return self.baseurl

	#======================================
	def getHourUrl(self):
		"""
		Placeholder method for getting an hour-specific URL. Currently returns the base URL.

		Returns:
			str: URL for data.
		"""
		return self.getUrl()

	#======================================
	def getCurrentComedRate(self, data=None):
		"""
		Calculates the current average ComEd rate.

		Args:
			data (list, optional): Raw JSON data as a list of dictionaries. Defaults to None.

		Returns:
			float: The average rate for the most recent hour.
		"""
		if data is None:
			data = self.downloadComedJsonData()
		yvalues = self.parseComedData(data)
		x2 = sorted(yvalues.keys())
		key = x2[-1]
		ylist = yvalues[key]
		yarray = numpy.array(ylist, dtype=numpy.float64)
		ypositive = numpy.where(yarray < 1.0, 1.0, yarray)
		return ypositive.mean()

	#======================================
	def getMostRecentRate(self, data=None):
		"""
		Returns the most recent rate from the data.

		Args:
			data (list, optional): Raw JSON data. Defaults to None.

		Returns:
			float: The most recent rate.
		"""
		while data is None:
			data = self.downloadComedJsonData()
		yvalues = self.parseComedData(data)
		x2 = list(yvalues.keys())
		x2.sort()
		key = x2[-1]
		ylist = yvalues[key]
		return ylist[0]

	#======================================
	def getPredictedRate(self, data=None):
		"""
		Predicts the future rate based on the current trend using linear regression.

		Args:
			data (list, optional): Raw JSON data. Defaults to None.

		Returns:
			float: Predicted future rate.
		"""
		while data is None:
			data = self.downloadComedJsonData()
		median, std = self.getMedianComedRate()

		yvalues = self.parseComedData(data)
		x2 = list(yvalues.keys())
		x2.sort()

		key = x2[-1]
		ylist = yvalues[key]
		yarray = numpy.array(ylist, dtype=numpy.float64)
		ymean = yarray.mean()
		ypositive = numpy.where(yarray < 1.0, 1.0, yarray)
		ystd = ypositive.std()
		weight = min((8-len(ylist))/8., 1)
		if abs(key - float(int(key))) < 0.001:
			if self.debug is True:
				print((".. %03d:00 -> %2.2f +- %2.2f / %2.2f -> %.1f/%.1f"
					%(key, ymean, ystd, ystd*weight, yarray.min(), yarray.max())))
			pass
		value1 = ymean + math.sqrt(ystd)*weight

		if len(ypositive) > 3:
			yslopedata = numpy.flip(ypositive, axis=0)
		else:
			key2 = x2[-3]
			ylist2 = yvalues[key2]
			yarray2 = numpy.array(ylist2, dtype=numpy.float64)
			ypositive2 = numpy.where(yarray2 < 1.0, 1.0, yarray2)
			yslopedata = numpy.flip(numpy.hstack((ypositive, ypositive2[:4])), axis=0)
			xarray = numpy.arange(0,len(yslopedata))

		xarray = numpy.arange(0,len(yslopedata))
		slope, intercept, r_value, p_value, std_err = stats.linregress(xarray, yslopedata)
		if self.debug is True:
			print(yslopedata)
			print(xarray)
			print(".. Slope = {0:.3f}".format(slope))

		if slope < 0.1:
			slope = 0.1
		value2 = (14 - len(yslopedata))*slope/2.0 + yarray.mean()

		value3 = (yarray.max() + yarray.mean() + yarray[0])/3.0

		if self.debug is True:
			print(".. Value 1 = {0:.3f} (mean + std*weight)".format(value1))
			print(".. Value 2 = {0:.3f} (slope based)".format(value2))
			print(".. Value 3 = {0:.3f} (avg of: max, mean, recent)".format(value3))
		return max(value1, value2, value3)

	#======================================
	def getReasonableCutOff(self):
		"""
		Calculates a reasonable cutoff price for energy usage based on time of day, day of the week,
		and solar peak hours. Includes bonuses for weekends and late-night usage.

		Returns:
			float: The calculated reasonable cutoff price.
		"""
		if self.debug:
			print("\ngetReasonableCutOff():")

		chargingCutoffPrice = 10.1
		weekendBonus = 0.9
		lateNightBonus = 0.8
		peakSolarBonus = 1.5

		# Start calculating the cutoff
		if self.debug:
			print(f".. Starting cutoff {chargingCutoffPrice:.2f}c")

		median, std = self.getMedianComedRate()

		if self.debug:
			print(f".. Median Rate {median:.2f} +/- {std:.3f}c")

		# Calculate a default cutoff based on the median and standard deviation
		defaultCutoff = median + math.sqrt(std) / 5.0

		if self.debug:
			print(f".. Calculated Cutoff {defaultCutoff:.3f}c")

		reasonableCutoff = (chargingCutoffPrice + 2 * defaultCutoff) / 3.0

		if self.debug:
			print(f".. Combined Cutoff {reasonableCutoff:.3f}c")

		# Adjust the cutoff for weekends
		now = datetime.datetime.now()
		if now.weekday() >= 5:  # Saturday or Sunday
			if self.debug:
				print(f".. Sat/Sun weekend bonus of {weekendBonus:.2f}c")
			reasonableCutoff += weekendBonus

		# Adjust the cutoff for late-night usage
		if now.hour >= 23 or now.hour <= 5:
			if self.debug:
				print(f".. Late night bonus of {lateNightBonus:.2f}c")
			reasonableCutoff += lateNightBonus

		# Adjust the cutoff for peak solar hours
		if 6 <= now.hour <= 20:
			solar_adjust = math.exp(-1 * (now.hour - 12) ** 2 / 6.3) * peakSolarBonus
			if self.debug:
				print(f".. Peak solar bonus of {solar_adjust:.2f}c")
			reasonableCutoff += solar_adjust

		# Ensure the cutoff is not below 1.0
		if reasonableCutoff < 1.0:
			reasonableCutoff = 1.0

		if self.debug:
			print(f".. Final Cutoff {reasonableCutoff:.3f}c")

		return reasonableCutoff

	#======================================
	def getMedianComedRate(self, data=None):
		"""
		Calculates the 75th percentile (used as median) of the rates and the standard deviation.

		Args:
			data (list, optional): Raw JSON data. Defaults to None.

		Returns:
			tuple: A tuple containing the median (75th percentile) and the standard deviation of rates.
		"""
		if data is None:
			data = self.downloadComedJsonData()

		prices = [float(item['price']) for item in data]
		parray = numpy.array(prices, dtype=numpy.float64)

		# Check if median and standard deviation are cached
		if hasattr(self, '_median_cache'):
			return self._median_cache

		# Calculate the 75th percentile and standard deviation
		median = numpy.percentile(parray, 75)
		std = numpy.std(parray)
		self._median_cache = (median, std)

		if self.debug:
			print(f".. 24 hour median price: {median:.3f} +/- {std:.3f}")

		return median, std

#======================================
#======================================
#======================================
#======================================
if __name__ == '__main__':
	# Measure start time
	start_time = time.time()

	# Instantiate the ComedLib object
	comedlib = ComedLib()
	comedlib.debug = True  # Enable debugging output

	# Calculate and print the 24-hour median rate
	medrate, std = comedlib.getMedianComedRate()
	print(f"24hr Median Rate    {medrate:.3f}c +- {std:.3f}c")

	# Calculate and print the current rate
	currrate = comedlib.getCurrentComedRate()
	print(f"Hour Current Rate   {currrate:.3f}c")

	# Calculate and print the predicted future rate
	predictrate = comedlib.getPredictedRate()
	print(f"Hour Predicted Rate {predictrate:.3f}c")

	# Calculate and print the reasonable cutoff
	cutoffrate = comedlib.getReasonableCutOff()
	print(f"Reasonable Cutoff   {cutoffrate:.3f}c")

	# Determine and print the house usage status based on the current rate and cutoff
	if currrate > cutoffrate:
		print("House Usage Status  OFF")
	else:
		print("House Usage Status  on")

	# Measure end time and print run-time duration
	end_time = time.time()
	print(f"Script run time: {end_time - start_time:.2f} seconds")


