#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import datetime
import os
class Logger():
	def __init__(self, logfile):
		self.logfile = open(logfile, "w")
	
	def log(self, text,level="i"):
		if level == "i":
			level = "[INFO]"
		elif level == "w":
			level = "[WARN]"
		elif level == "e":
			level = "[ERROR]"
		
		if type(text) != str:
			self.logfile.write(level+" "+str(datetime.datetime.now())+" "+str(text)+"\n")
			self.logfile.flush()
			os.fsync(self.logfile.fileno())
		else:
			self.logfile.write(level+" "+str(datetime.datetime.now())+" "+text+"\n")
			self.logfile.flush()
			os.fsync(self.logfile.fileno())
	
	def __del__(self):
		self.logfile.close()