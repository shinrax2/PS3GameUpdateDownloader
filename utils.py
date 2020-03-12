#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#
# PS3GameUpdateDownloader by shinrax2

#built-in
import datetime
import os
import platform
import json

class Logger():
    def __init__(self, logfile, window=None):
        self.logfile = open(logfile, "w")
        if window != None:
            self.window = window
        else:
            self.window = None
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

class Loc():
    def __init__(self):
        self.locList = []
        self.locDir = "./loc/"
        self.currentLoc = {}
        self._scanForLoc()
        self.setLoc()

    def _scanForLoc(self):
        locFiles = [pos_json for pos_json in os.listdir(self.locDir) if pos_json.endswith('.json')]
        for loc in locFiles:
            with open(os.path.join(self.locDir,loc), "r", encoding="utf8") as j:
                l = json.loads(j.read())
            self.locList.append({"language_name":l["language_name"], "language_short":l["language_short"]})
            del(l)
    
    def getLocs(self):
        return self.locList
        
    def getLoc(self):
        return self.currentLoc["language_short"]
        
    def setLoc(self, loc=None):
        if loc != None:
            for l in self.locList:
                if l["language_short"] == loc:
                    with open(os.path.join(self.locDir, (l["language_short"]+".json")), "r", encoding="utf8") as f:
                        self.currentLoc = json.loads(f.read())
        else:
            with open(os.path.join(self.locDir, "./en.json"), "r", encoding="utf8") as f:
                self.currentLoc = json.loads(f.read())
                
    def getKey(self, key, args=[]):
        try:
            return massFormat(self.currentLoc[key], args)
        except KeyError:
            return "ERROR \""+key+"\""

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
    
def massFormat(stri, args):
    call = "stri.format( "
    for a in args:
        call = call+"'"+str(a)+"', "
    if call.endswith(","):
        call = call[:-1]+")"
    else:
        call = call+")"
    return eval(call, {}, locals())

def filterIllegalCharsFilename(path):
    if platform.system() == "Windows":
        return massReplace([":","/","\\","*","?","<",">","\"","|"], "", path)
    elif platform.system() == "Linux":
        return massReplace(["/", "\x00"], "", path)
    elif platform.system() == "Darwin":
        return massReplace(["/", "\x00", ":"], "", path)
