#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#
# PS3GameUpdateDownloader by shinrax2


#built-in
import datetime
import os
import platform
import json
import urllib.parse
import tempfile
import shutil
import zipfile
import subprocess
import sys
import setuptools
import shlex
import traceback
import hashlib

#pip packages
import requests

#local files
import PS3GUD

class Logger():
    def __init__(self, window=None):
        logdir = "./logs"
        now = str(datetime.datetime.now()).split(".")[0].replace(" ", "_").replace(":", "-")
        if os.path.exists(logdir) == False:
            os.mkdir(logdir)
        logfile = os.path.join(logdir, "log-"+now+".txt")
        self.logfile = open(logfile, "w", encoding="utf8")
        if window != None:
            self.window = window
        else:
            self.window = None
            
    def log(self, text, level="i"):
        if level == "i":
            level = "[INFO]"
        elif level == "w":
            level = "[WARN]"
        elif level == "e":
            level = "[ERROR]"
        
        if type(text) != str:
            text = str(text)
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
            self.locList.append({"language_name":l["language_name"]["string"], "language_short":l["language_short"]["string"]})
            del(l)
    
    def getLocs(self):
        return self.locList
        
    def getLoc(self):
        return self.getKey("language_short")
        
    def setLoc(self, loc=None):
        if loc != None:
            for l in self.locList:
                if l["language_short"] == loc:
                    with open(os.path.join(self.locDir, (l["language_short"]+".json")), "r", encoding="utf8") as f:
                        self.currentLoc = json.loads(f.read())
        else:
            with open(os.path.join(self.locDir, "./en.json"), "r", encoding="utf8") as f:
                self.fallbackLoc = json.loads(f.read())
                self.currentLoc = self.fallbackLoc
                
    def getKey(self, key, args=[]):
        try:
            return massFormat(self.currentLoc[key]["string"], args)
        except KeyError:
            try:
                return massFormat(self.fallbackLoc[key]["string"], args)
            except KeyError:
                return "ERROR \""+key+"\""

class UpdaterGithubRelease():
    def __init__(self, releaseFile):
        self.rF = releaseFile
        self.release = {}
        self.resp = {}
        with open(self.rF, "r", encoding="utf8") as f:
            self.release = json.loads(f.read())
        ps3 = PS3GUD.PS3GUD()
        ps3.setLoc(Loc())
        ps3.loadConfig()
        self.proxies = ps3.proxies
            
    def getVersion(self):
        return self.release["version"]
        
    def getCommitID(self):
        try:
            return self.release["commitid"]
        except KeyError:
            return "None"

    def getChangelog(self):
        #returns text body from latest github release without formatting characters 
        return massReplace(["```"], "", self.resp["body"])
        
    def getRightAssetNum(self):
        num = 0
        for asset in self.resp["assets"]:
            if asset["browser_download_url"].endswith(getArchiveSuffix()+".zip"):
                return num
            num += 1
        return -1
        
    def getRightAssetNumSHA256(self):
        num = 0
        for asset in self.resp["assets"]:
            if asset["browser_download_url"].endswith(getArchiveSuffix()+".zip.sha256"):
                return num
            num += 1
        return -1
    
    def checkForNewRelease(self):
        try:
            url = urllib.parse.urljoin(urllib.parse.urljoin(urllib.parse.urljoin("https://api.github.com/repos/" ,self.release["author"]+"/"), self.release["repo"]+"/"), "releases/latest")
            resp = requests.get(url, proxies=self.proxies)
            data = resp.content
            self.resp = json.loads(data)
        except requests.exceptions.ConnectionError:
            return False
        if self.release["version"] < self.resp["tag_name"]:
            assetnum = self.getRightAssetNum()
            if assetnum > -1:
                rel = {}
                rel["version"] = self.resp["tag_name"]
                rel["releaseUrlWeb"] = urllib.parse.urljoin(urllib.parse.urljoin(urllib.parse.urljoin("https://github.com/" ,self.release["author"]+"/"), self.release["repo"]+"/"), "releases/latest")
                rel["releaseUrlDl"] = self.resp["assets"][assetnum]["browser_download_url"]
            else:
                return 2
            return rel
        else:
            return 1
            
    def downloadNewRelease(self, cwd, window):
        text = window["updater_text"]
        bar = window["updater_progressbar"]
        tdir = tempfile.gettempdir()
        url = self.resp["assets"][self.getRightAssetNum()]["browser_download_url"]
        shaurl = self.resp["assets"][self.getRightAssetNumSHA256()]["browser_download_url"]
        local_filename = os.path.join(tdir, os.path.basename(url))
        chunk_size=8192
        count = 0
        already_loaded = 0
        with requests.get(url, stream=True, proxies=self.proxies) as r:
            r.raise_for_status()
            size = int(r.headers["content-length"])
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=chunk_size): 
                    if chunk:
                        f.write(chunk)
                        count += 1
                        already_loaded = count * chunk_size
                        if already_loaded / size > 1:
                            already_loaded = size
                        label = "Downloading update: "+formatSize(already_loaded)+"/"+formatSize(size)
                        percentage = already_loaded / size * 100
                        text.Update(label)
                        bar.UpdateBar(percentage)
                        window.Refresh()
        if int(os.path.getsize(local_filename)) == int(self.resp["assets"][0]["size"]):
            text.Update("Verifying update")
            window.Refresh()
            if requests.get(shaurl, proxies=self.proxies).content.decode("ascii") == sha256File(local_filename):
                text.Update("Backing up stuff")
                window.Refresh()
                #backup config and downloadedPKGs
                if os.path.exists(os.path.join(cwd, "config.json")) and os.path.isfile(os.path.join(cwd, "config.json")):
                    shutil.copy2(os.path.join(cwd, "config.json"), os.path.join(tdir, "config.json"))
                if os.path.exists(os.path.join(tdir, "downloadedPKGs")) and os.path.isdir(os.path.join(tdir, "downloadedPKGs")):
                    shutil.rmtree(os.path.join(tdir, "downloadedPKGs"))
                if os.path.exists(os.path.join(cwd, "downloadedPKGs")) and os.path.isdir(os.path.join(cwd, "downloadedPKGs")):
                    shutil.copytree(os.path.join(cwd, "downloadedPKGs"), os.path.join(tdir, "downloadedPKGs"))
                    
                rmDirContents(cwd)
                
                tzipdir = os.path.join(tdir, "PS3GUDUpdate")
                if os.path.exists(tzipdir) == False and os.path.isfile(tzipdir) == False:
                    os.mkdir(tzipdir)
                text.Update("Extracting update")
                window.Refresh()
                with zipfile.ZipFile(local_filename, "r") as zipf:
                    zipf.extractall(tzipdir)
                if len(os.listdir(tzipdir)) == 1:
                        if os.path.isdir(os.path.join(tzipdir, os.listdir(tzipdir)[0])):
                            copysrc = os.path.join(tzipdir, os.listdir(tzipdir)[0])
                        else:
                            copysrc = tzipdir
                else:
                    copysrc = tzipdir
                text.Update("Installing update")
                window.Refresh()
                setuptools.distutils.dir_util.copy_tree(copysrc, cwd)
                            
                text.Update("Restoring backedup stuff and cleaning up")
                window.Refresh()
                #restore config and downloadedPKGs
                if os.path.exists(os.path.join(tdir, "config.json")) and os.path.isfile(os.path.join(tdir, "config.json")):
                    shutil.copy2(os.path.join(tdir, "config.json"), os.path.join(cwd, "config.json"))
                    os.remove(os.path.join(tdir, "config.json"))
                if os.path.exists(os.path.join(tdir, "downloadedPKGs")) and os.path.isdir(os.path.join(tdir, "downloadedPKGs")):
                    shutil.copytree(os.path.join(tdir, "downloadedPKGs"), os.path.join(cwd, "downloadedPKGs"))
                    shutil.rmtree(os.path.join(tdir, "downloadedPKGs"))
                os.remove(local_filename)
                os.remove(os.path.join(tdir, "PS3GUDUpdate.json"))
                shutil.rmtree(tzipdir)
                
    def startUpdater(self):
        suffix = getExecutableSuffix()
        if isAppFrozen():
            file = "PS3GUDup"+suffix
        else:
            file = "updater"+suffix
        
        #write current install dir to tempfile
        data = {"dir": os.getcwd()}
        with open(os.path.join(tempfile.gettempdir(), "PS3GUDUpdate.json"), "w", encoding="utf8") as f:
            f.write(json.dumps(data, sort_keys=True, indent=4))
        #copy updater
        shutil.copy2(os.path.join(os.getcwd(), file), os.path.join(tempfile.gettempdir(), file))
        if isAppFrozen() == False:
            #copy depency if app not compiled
            shutil.copy2(os.path.join(os.getcwd(), "utils.py"), os.path.join(tempfile.gettempdir(), "utils.py"))
            shutil.copy2(os.path.join(os.getcwd(), "PS3GUD.py"), os.path.join(tempfile.gettempdir(), "PS3GUD.py"))
        
        if isAppFrozen() == False:
            if platform.system() == "Windows":
                subprocess.Popen("py "+os.path.join(tempfile.gettempdir(), file))
            if platform.system() == "Linux":
                subprocess.Popen(shlex.split("python3 "+os.path.join(tempfile.gettempdir(), file)))
        else:
                subprocess.Popen(os.path.join(tempfile.gettempdir(), file))
        sys.exit()
        

def formatSize(size):
    if float(size) > 1024-1 and float(size) < 1024*1024 : #KiB
        return str(format(float(size)/1024, '.2f'))+"KiB"
    elif float(size) > 1024*1024-1 and float(size) < 1024*1024*1024: #MiB
        return str(format(float(size)/1024/1024, '.2f'))+"MiB"
    elif float(size) > 1024*1024*1024-1: #GiB
        return str(format(float(size)/1024/1024/1024, '.2f'))+"GiB"
    else: #Bytes
        return str(size)+"B"
        
def massReplace(find, replace, stri):
    out = stri
    for item in find:
        out = out.replace(item, replace)
    return out
    
def massFormat(stri, args):
    #basically str.format() that takes a list of arguments
    #!!very hacky, please tell me if you know a better way!!
    call = "stri.format( "
    for a in args:
        call = call+"'"+massReplace(["\"", "'"], "", str(a))+"', "
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
            
def isAppFrozen():
    #check if app was compiled with pyinstaller
    if getattr(sys, "frozen", False):
        state = True
    else:
        state = False
    return state
    
def getExecutableSuffix():
    #get right suffix for starting updater, etc.
    suffix = ""
    if isAppFrozen():
        if platform.system() == "Windows":
            suffix = ".exe"
    else:
        suffix = ".py"
    return suffix

def getArchiveSuffix():
    #get right archive for downloading new updates
    if isAppFrozen():
        if platform.system() == "Windows":
            suffix = "win"
        elif platform.system() == "Linux":
            suffix = "linux"
        if platform.architecture()[0] == "32bit":
            suffix += "32"
        elif platform.architecture()[0] == "64bit":
            suffix += "64"
    else:
        suffix = "source"
    return suffix

def logUncaughtException(exctype, value, tb):
    now = str(datetime.datetime.now()).split(".")[0].replace(" ", "_").replace(":", "-")
    if os.path.exists("logs") == False:
        os.mkdir("logs")
    with open(os.path.join("logs", "Crash-"+now+".txt"), "w") as f:
        f.write("Uncaught exception:\nType: "+str(exctype)+"\nValue: "+str(value)+"\nTraceback:\n")
        for item in traceback.format_list(traceback.extract_tb(tb)):
            f.write(item)

def cleanupAfterUpdate():
    suffix = getExecutableSuffix()
    if os.path.exists(os.path.join(tempfile.gettempdir(), "PS3GUDup"+suffix)) and os.path.isfile(os.path.join(tempfile.gettempdir(), "PS3GUDup"+suffix)):
        os.remove(os.path.join(tempfile.gettempdir(), "PS3GUDup"+suffix)) 
    if os.path.exists(os.path.join(tempfile.gettempdir(), "PS3GUDUpdate.json")) and os.path.isfile(os.path.join(tempfile.gettempdir(), "PS3GUDUpdate.json")):
        os.remove(os.path.join(tempfile.gettempdir(), "PS3GUDUpdate.json")) 
    if isAppFrozen() == False:
        if os.path.exists(os.path.join(tempfile.gettempdir(), "utils.py")) and os.path.isfile(os.path.join(tempfile.gettempdir(), "utils.py")):
            os.remove(os.path.join(tempfile.gettempdir(), "utils.py"))
        if os.path.exists(os.path.join(tempfile.gettempdir(), "PS3GUD.py")) and os.path.isfile(os.path.join(tempfile.gettempdir(), "PS3GUD.py")):
            os.remove(os.path.join(tempfile.gettempdir(), "PS3GUD.py"))

def sha256File(file):
    hash = hashlib.sha256()
    with open(file, "rb") as f:
        for block in iter(lambda: f.read(4096), b""):
            hash.update(block)
    return hash.hexdigest()
