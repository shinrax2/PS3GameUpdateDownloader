#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#
# PS3GameUpdateDownloader by shinrax2

#built-in
import datetime
import os
import platform

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
        
def formatSize(size):
    if int(size) > 1024-1 and int(size) < 1024*1024 : #KB
        return str(format(float(size)/1024, '.2f'))+"KB"
    elif int(size) > 1024*1024-1 and int(size) < 1024*1024*1024: #MB
        return str(format(float(size)/1024/1024, '.2f'))+"MB"
    elif int(size) > 1024*1024*1024-1: #GB
        return str(format(float(size)/1024/1024/1024, '.2f'))+"GB"
    else: #Bytes
        return str(size)+"B"
        
def massReplace(find, replace, str):
    out = str
    for item in find:
        out = out.replace(item, replace)
    return out

def filterIllegalCharsFilename(path):
    if platform.system() == "Windows":
        return massReplace([":","/","\\","*","?","<",">","\"","|"], "", path)
    elif platform.system() == "Linux":
        return massReplace(["/", "\x00"], "", path)
    elif platform.system() == "Darwin":
        return massReplace(["/", "\x00", ":"], "", path)
