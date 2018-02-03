
import os
import re
import sys
import glob
import math
import time
import types
import numpy
import random
import string
import shutil
import urllib
import subprocess
import unicodedata

"""
File for common functions to musiclib, movielib, and photolib
"""


class CommonLib(object):
	#=======================
	def humantime(self, secs):
		mins, secs = divmod(secs, 60)
		hours, mins = divmod(mins, 60)
		days, hours = divmod(hours, 24)
		if days > 0:
			return '%02dd:%02dh' % (days, hours)
		elif hours > 0:
			return '%02dh:%02dm' % (hours, mins)
		elif mins > 0:
			return '%02dm:%02ds' % (mins, secs)
		elif secs > 0.2:
			return '%.1fs' % (secs)
		else:
			return '%.1es' % (secs)

	#=======================
	def isint(self, n):
		if re.search("^\d+$", n):
			return True
		return False

	#=======================
	def extraCleanName(self, f):
		g = self.cleanName(f)
		if g is None:
			return 'None'
		g = self.cleanName(g.lower())
		if g is None:
			return 'None'
		g = re.sub("_", "", g)
		g = re.sub("-", "", g)
		g = g.lower()
		return g
	
	#=======================
	def compareStrings(self, s1, s2):
		size = max(len(s1), len(s2))
		return self.levenshtein(s1, s2)/float(size)
	
	#=======================
	def levenshtein(self, s1, s2):
		if len(s1) < len(s2):
			return self.levenshtein(s2, s1)
		if not s1:
			return len(s2)

		previous_row = xrange(len(s2) + 1)
		for i, c1 in enumerate(s1):
			current_row = [i + 1]
			for j, c2 in enumerate(s2):
				insertions = previous_row[j + 1] + 1 # j+1 instead of j since previous_row and current_row are one character longer
				deletions = current_row[j] + 1       # than s2
				substitutions = previous_row[j] + (c1 != c2)
				current_row.append(min(insertions, deletions, substitutions))
			previous_row = current_row

		return previous_row[-1]

	#=======================
	def cleanName(self, f, cut=True):
		specials = { "!!!": "ChkChkChk", "!": "Exclaim",
			"*": "Asterix", "( )": "Parens", "+/-": "PlusMinus", }
		words = ['of', 'the', 'a', 'in', 'for', 'am', 'is', 'on',
			'to', 'than', 'with', 'by', 'from', 'or', 'and',
		]
		if f is None:
			return None
		g = f.strip()
		if g in specials:
			return specials[g]
		if len(g) < 1:
			return None
		g = self.unicodeToString(g)
		g = re.sub(" ", "_", g)
		g = re.sub("\'", "", g)
		g = re.sub("\"", "", g)
		g = re.sub("\]", "_", g)
		g = re.sub("\[", "_", g)

		g = re.sub("^the_", "", g, re.IGNORECASE)
		g = re.sub("^an_", "", g, re.IGNORECASE)
		g = re.sub("^a_", "", g, re.IGNORECASE)
		g = re.sub("^The_", "", g, re.IGNORECASE)
		g = re.sub("^An_", "", g, re.IGNORECASE)
		g = re.sub("^A_", "", g, re.IGNORECASE)
		g = re.sub("&", "and", g)

		g = re.sub("[^a-zA-z0-9_-]", "_", g)
		for word in words:
			a = re.search("_("+word+")_", g, re.IGNORECASE)
			if a:
				for inword in a.groups():
					g = re.sub("_"+inword+"_", "_"+word+"_", g)
		g = re.sub("[_ ]feat[_ ][a-zA-Z0-9 _-]*$", "and", g)
		g = re.sub("[_ ]featuring[_ ][a-zA-Z0-9 _-]*$", "and", g)
		g = re.sub("[_ ]ft[_ ][a-zA-Z0-9 _-]*$", "and", g)

		if re.search('[^a-z]feat[^a-z]', g):
			print g

		g = re.sub("\^", "_", g)
		g = re.sub(",", "_", g)
		g = re.sub("^-", "", g)
		g = re.sub("_-", "-", g)
		g = re.sub("-_", "-", g)
		g = re.sub("__", "_", g)
		g = re.sub("__", "_", g)
		g = re.sub("_*$", "", g)
		g = re.sub("^_*", "", g)
		g = re.sub("^-*", "", g)
		if g == "unknown":
			return None
		if re.search('[^a-zA-z0-9_-]', g):
			print "\033[1;32mWeird character: "+g+"\033[0m"
			time.sleep(2)
		if len(g) == 0:
			print "\033[31mERROR: "+f+"\033[0m"
			return None
			sys.exit(1)
		if cut is True and len(g) > 40:
			if re.search("_[0-9]*$", g):
				g = re.sub("_[0-9]*$", "", g)
			g = g[:40]
		g = re.sub("_*$", "", g)
		if len(g) < 1:
			return None
		elif len(g) < 2:
			return g
		g = g[0].upper()+g[1:]
		return g

	#===============
	def getMountPoint(self, filename):
		"""
		returns file or directory mount point
		"""
		path = os.path.abspath(filename)
		while not os.path.ismount(path):
			path = os.path.dirname(path)
		return path

	#===============
	def fileSize(self, filename):
		"""
		return file size in bytes
		"""
		if not os.path.isfile(filename):
			return 0
		stats = os.stat(filename)
		size = stats[6]
		return size

	#=======================
	def unicodeToString(self, uni):
		if not isinstance(uni, str) and not isinstance(uni, unicode):
			try:
				uni = uni.decode("utf8")
			except AttributeError:
				uni = uni.text[0]
		try:
			uni = unicode(uni)
			string = unicodedata.normalize('NFKD', uni)
		except UnicodeDecodeError:
			print uni
			string = uni
		string = str(string.encode('ascii', 'ignore'))
		return string

	#===============
	def md5sumfile(self, filename):
		"""
		Returns an md5 hash for file filename
		"""
		if not os.path.isfile(filename):
			apDisplay.printError("MD5SUM, file not found: "+filename)
		f = file(filename, 'rb')
		#this next library is deprecated in python 2.6+, need to use hashlib
		import hashlib
		m = hashlib.md5()
		while True:
			d = f.read(8096)
			if not d:
				break
			m.update(d)
		f.close()
		return m.hexdigest()

	#===============
	def quickmd5(self, filename):
		"""
		Returns a quick md5 hash for file filename
		"""
		if not os.path.isfile(filename):
			print self.colorString("MD5SUM, file not found: "+filename, "red")
			sys.exit(1)
		f = file(filename, 'rb')
		#this next library is deprecated in python 2.6+, need to use hashlib
		import hashlib
		m = hashlib.md5()
		for i in range(9):
			d = f.read(8096)
			if not d:
				break
			m.update(d)
			f.seek(8096)
		f.close()
		return m.hexdigest()

	#=======================
	def getNumFilesInDir(self, dirname):
		absdirname = os.path.abspath(dirname)
		if not os.path.isdir(absdirname):
			return 0
		files = glob.glob(os.path.join(absdirname, "*.*"))
		return len(files)

	#=======================
	def getFiles(self, depth=6, extlist=[], folder=None, shuffle=False):
		files = []
		for ext in extlist:
			sstr = "*."+ext
			for i in range(depth+1):
				if folder is not None:
					sstr2 = os.path.join(folder, sstr)
				else:
					sstr2 = sstr
				files.extend(glob.glob(sstr2))
				sstr = "*/"+sstr
		files.sort()
		if shuffle is True:
			random.shuffle(files)
		print "Found %d files"%(len(files))
		return files

	#=======================
	def rightPadString(self, s,n=10,fill=" "):
		n = int(n)
		s = str(s)
		if(len(s) > n):
			return s[:n]
		while(len(s) < n):
			s += fill
		return s

	#=======================
	def leftPadString(self, s,n=10,fill=" "):
		n = int(n)
		s = str(s)
		if(len(s) > n):
			return s[:n]
		while(len(s) < n):
			s = fill+s
		return s

	#=======================
	def colorString(self, text, fg=None, bg=None):
		"""Return colored text.
		Uses terminal color codes; set avk_util.enable_color to 0 to
		return plain un-colored text. If fg is a tuple, it's assumed to
		be (fg, bg). Both colors may be 'None'.
		"""
		colors = {
			"black" :"30",
			"red"   :"31",
			"green" :"32",
			"brown" :"33",
			"orange":"33",
			"blue"  :"34",
			"violet":"35",
			"purple":"35",
			"magenta":"35",
			"maroon":"35",
			"cyan"  :"36",
			"lgray" :"37",
			"gray"  :"1;30",
			"lred"  :"1;31",
			"lgreen":"1;32",
			"yellow":"1;33",
			"lblue" :"1;34",
			"pink"  :"1;35",
			"lcyan" :"1;36",
			"white" :"1;37"
		}
		if fg is None:
			return text
		if type(fg) in (types.TupleType, types.ListType):
			fg, bg = fg
		if not fg:
			return text
		opencol = "\033["
		closecol = "m"
		clear = opencol + "0" + closecol
		xterm = 0
		if os.environ.get("TERM") is not None and os.environ.get("TERM") == "xterm": 
			xterm = True
		else:
			xterm = False
		b = ''
		# In xterm, brown comes out as yellow..
		if xterm and fg == "yellow": 
			fg = "brown"
		f = opencol + colors[fg] + closecol
		if bg:
			if bg == "yellow" and xterm: 
				bg = "brown"
			try: 
				b = colors[bg].replace('3', '4', 1)
				b = opencol + b + closecol
			except KeyError: 
				pass
		return "%s%s%s%s" % (b, f, text, clear)



