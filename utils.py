#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import datetime
import os
class Logger():
    def __init__(self, logfile, window=None):
        self.logfile = open(logfile, "w")
        if window != None:
            self.window = window
    def log(self, text,level="i"):
        if level == "i":
            level = "[INFO]"
        elif level == "w":
            level = "[WARN]"
        elif level == "e":
            level = "[ERROR]"
        
        if type(text) != str:
            log = level+" "+str(datetime.datetime.now())+" "+str(text)
            if self.window != None:
                print(log)
                self.window.Refresh()
            self.logfile.write(log+"\n")
            self.logfile.flush()
            os.fsync(self.logfile.fileno())
        else:
            log = level+" "+str(datetime.datetime.now())+" "+text
            if self.window != None:
                print(log)
                self.window.Refresh()
            self.logfile.write(log+"\n")
            self.logfile.flush()
            os.fsync(self.logfile.fileno())
    
    def __del__(self):
        self.logfile.close()