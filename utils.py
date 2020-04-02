#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#
# PS3GameUpdateDownloader by shinrax2

#built-in
import datetime
import os
import platform
import json
import urllib.request
import urllib.parse
import tempfile
import shutil
import zipfile
import subprocess
import sys
#pip packages
import requests

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

class UpdaterGithubRelease():
    def __init__(self, releaseFile):
        self.rF = releaseFile
        self.release = {}
        self.resp = {}
        with open(self.rF, "r", encoding="utf8") as f:
            self.release = json.loads(f.read())
            
    def getVersion(self):
        return self.release["version"]
        
    def getChangelog(self):
        return self.resp["body"]
        
    def getRightAssetNum(self):
        num = 0
        for asset in self.resp["assets"]:
            if asset["browser_download_url"].endswith(getArchiveSuffix()+".zip"):
                return num
            num += 1
    
    def checkForNewRelease(self):
        try:
            resp = urllib.request.urlopen(urllib.parse.urljoin(urllib.parse.urljoin(urllib.parse.urljoin("https://api.github.com/repos/" ,self.release["author"]+"/"), self.release["repo"]+"/"), "releases/latest"))
            data = resp.read()
            data.decode("utf-8")
            self.resp = json.loads(data)
        except urllib.error.HTTPError:
            return False
        if self.release["version"] < self.resp["tag_name"]:
            rel = {}
            rel["version"] = self.resp["tag_name"]
            rel["releaseUrlWeb"] = urllib.parse.urljoin(urllib.parse.urljoin(urllib.parse.urljoin("https://github.com/" ,self.release["author"]+"/"), self.release["repo"]+"/"), "releases/latest")
            rel["releaseUrlDl"] = self.resp["assets"][self.getRightAssetNum()]["browser_download_url"]
            return rel
        else:
            return 1
            
    def downloadNewRelease(self, cwd):
        tdir = tempfile.gettempdir()
        url = self.resp["assets"][0]["browser_download_url"]
        #cwd = os.getcwd()
        local_filename = os.path.join(tdir, os.path.basename(url))
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): 
                    if chunk:
                        f.write(chunk)
        if int(os.path.getsize(local_filename)) == int(self.resp["assets"][0]["size"]):
            #backup config and downloadedPKGs
            if os.path.exists(os.path.join(cwd, "config.json")) and os.path.isfile(os.path.join(cwd, "config.json")):
                shutil.copy2(os.path.join(cwd, "config.json"), os.path.join(tdir, "config.json"))
            if os.path.exists(os.path.join(cwd, "./downloadedPKGs")) and os.path.isdir(os.path.join(cwd, "./downloadedPKGs")):
                shutil.copy2(os.path.join(cwd, "./downloadedPKGs"), os.path.join(tdir, "./downloadedPKGs"))
                
            rmDirContents(cwd)
            
            tzipdir = os.path.join(tdir, "PS3GUDUpdate")
            if os.path.exists(tzipdir) == False and os.path.isfile(tzipdir) == False:
                os.mkdir(tzipdir)
            copysrc = ""
            with zipfile.ZipFile(local_filename, "r") as zipf:
                zipf.extractall(tzipdir)
            if len(os.listdir(tzipdir)) == 1:
                    if os.path.isdir(os.path.join(tzipdir, os.listdir(tzipdir)[0])):
                        copysrc = os.path.join(tzipdir, os.listdir(tzipdir)[0])
            else:
                copysrc = tzipdir
            for item in os.listdir(copysrc):
                if os.path.isfile(os.path.join(copysrc, item)):
                    shutil.copy(os.path.join(copysrc, item), cwd)
                elif os.path.isdir(os.path.join(copysrc, item)):
                    os.mkdir(os.path.join(cwd, item))
                    for item2 in os.listdir(os.path.join(copysrc, item)):
                        shutil.copy(os.path.join(os.path.join(copysrc, item), item2), os.path.join(cwd, item))
                        
            #restore config and downloadedPKGs
            if os.path.exists(os.path.join(tdir, "config.json")) and os.path.isfile(os.path.join(tdir, "config.json")):
                shutil.copy2(os.path.join(tdir, "config.json"), os.path.join(cwd, "config.json"))
                os.remove(os.path.join(tdir, "config.json"))
            if os.path.exists(os.path.join(tdir, "./downloadedPKGs")) and os.path.isdir(os.path.join(tdir, "./downloadedPKGs")):
                shutil.copy2(os.path.join(tdir, "./downloadedPKGs"), os.path.join(cwd, "./downloadedPKGs"))
                shutil.rmtree(os.path.join(tdir, "./downloadedPKGs"))
            os.remove(local_filename)
            os.remove(os.path.join(tdir, "PS3GUDUpdate.json"))
            shutil.rmtree(tzipdir)
            
    def startUpdater(self):
        data = {"dir": os.getcwd()}
        with open(os.path.join(tempfile.gettempdir(), "PS3GUDUpdate.json"), "w", encoding="utf8") as f:
            f.write(json.dumps(data, sort_keys=True, indent=4))
        suffix = getExecutableSuffix()
        shutil.copy2(os.path.join(os.getcwd(), "PS3GUDup"+suffix), os.path.join(tempfile.gettempdir(), "PS3GUDup"+suffix))
        subprocess.Popen(os.path.join(tempfile.gettempdir(), "PS3GUDup"+suffix))
        sys.exit()
        

def formatSize(size):
    if int(size) > 1024-1 and int(size) < 1024*1024 : #KB
        return str(format(float(size)/1024, '.2f'))+"KB"
    elif int(size) > 1024*1024-1 and int(size) < 1024*1024*1024: #MB
        return str(format(float(size)/1024/1024, '.2f'))+"MB"
    elif int(size) > 1024*1024*1024-1: #GB
        return str(format(float(size)/1024/1024/1024, '.2f'))+"GB"
    else: #Bytes
        return str(size)+"B"
        
def massReplace(find, replace, stri):
    out = stri
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
        
def rmDirContents(folder_path):
    for file_object in os.listdir(folder_path):
        file_object_path = os.path.join(folder_path, file_object)
        if os.path.isfile(file_object_path) or os.path.islink(file_object_path):
            os.unlink(file_object_path)
        else:
            shutil.rmtree(file_object_path)

def getExecutableSuffix():
    if platform.system() == "Windows":
        return ".exe"
    elif platform.system() == "Darwin":
        return ".app" #?
    else:
        return ""

def getArchiveSuffix():
    if platform.system() == "Windows":
        suffix = "win"
    elif platform.system() == "Darwin":
        suffix = "darwin"
    elif platform.system() == "Linux":
        suffix = "linux"
    if platform.architecture()[0] == "32bit":
        suffix += "32"
    elif platform.architecture()[0] == "64bit":
        suffix += "64"
    return suffix
