#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#
# PS3GameUpdateDownloader by shinrax2

#built-in
import urllib.parse
import ssl
import xml.etree.ElementTree as ET
import os
import hashlib
import sys
import shutil
import json
import time

#local files
import utils

#pip packages
import requests
import keyring

class PS3GUD():
    def __init__(self, window=None):
        if window != None:
            self.logger = utils.Logger(window)
        else:
            self.logger = utils.Logger()
        self.configFile = "./config.json"
        self.config = {}
        self.Updates = {}
        self.DlList = Queue()
        self.titleid = ""
        self.proxies = {}
        
        self.useDefaultConfig = True
        self.configDefaults = {}
        self.configDefaults["dldir"] = "./downloadedPKGs"
        self.configDefaults["verify"] = True
        self.configDefaults["checkIfAlreadyDownloaded"] = True
        self.configDefaults["storageThreshold"] = 95
        self.configDefaults["currentLoc"] = "en"
        self.configDefaults["checkForNewRelease"] = True
        self.configDefaults["use_proxy"] = False
        self.configDefaults["proxy_ip"] = ""
        self.configDefaults["proxy_port"] = ""
        self.configDefaults["proxy_user"] = ""
        self.configDefaults["proxy_pass"] = None
        self.configDefaults["dont_show_again_keyring_support"] = False
        
    def setWindow(self, window):
        self.logger.window = window
        
    def setLoc(self, loc):
        self.loc = loc

    def logHeader(self, version, psgversion):
        self.logger.log("PS3GameUpdateDownloader "+version)
        self.logger.log("Config File: "+self.configFile)
        self.logger.log("Language: "+ self.loc.getLoc())
        self.logger.log("Current working directory: "+os.getcwd())
        self.logger.log("Compiled: "+str(utils.isAppFrozen()))
        self.logger.log("PySimpleGUI version: "+psgversion)
        self.logger.log("Python version: "+sys.version)
        self.logger.log("\n")
        
    def loadConfig(self):
        if os.path.exists(self.configFile) and os.path.isfile(self.configFile):
            self.logger.log(self.loc.getKey("msg_configFileLoaded"))
            with open(self.configFile, "r", encoding="utf8") as f:
                self.config = json.loads(f.read())
            self.useDefaultConfig = False
            if self.config["use_proxy"] == True:
                self.config["proxy_pass"] = self.getProxyPass()
            else:
                self.config["proxy_pass"] = None
            self.setupProxy()
        else:
            self.logger.log(self.loc.getKey("msg_noConfigFile"))
            self.config = self.configDefaults
            
    def setConfig(self, config):
        self.config = config
        self.saveConfig()
        
    def saveConfig(self):
        with open(self.configFile, "w", encoding="utf8") as f:
            f.write(json.dumps(self.config, sort_keys=True, indent=4, ensure_ascii=False))
        self.logger.log(self.loc.getKey("msg_configFileSaved"))
        self.useDefaultConfig = False 
        
    def setProxyPass(self, pwd):
        keyring.set_password("ps3gud", "proxy_pass", pwd)
        self.config["proxy_pass"] = pwd
        
    def getProxyPass(self):
        return keyring.get_password("ps3gud", "proxy_pass")
        
    def setupProxy(self):
        if self.getConfig("use_proxy"):
            self.proxies["http"] = "socks5://"
            self.proxies["https"] = "socks5://"
            if self.getConfig("proxy_user") != "":
                self.proxies["http"] += self.getConfig("proxy_user")+":"
                self.proxies["https"] += self.getConfig("proxy_user")+":"
                if self.getConfig("proxy_pass") != None:
                    self.proxies["http"] += self.getConfig("proxy_pass")+"@"
                    self.proxies["https"] += self.getConfig("proxy_pass")+"@"
            self.proxies["http"] += self.getConfig("proxy_ip")+":"+self.getConfig("proxy_port")
            self.proxies["https"] += self.getConfig("proxy_ip")+":"+self.getConfig("proxy_port")
        else:
            self.proxies = {}
            
    def getConfig(self, key):
        try:
            return self.config[key]
        except KeyError:
            return self.configDefaults[key]
    
    def loadTitleDb(self, titledb = "titledb.json"):
        with open(titledb, "r", encoding="utf8") as f:
            data = json.loads(f.read())
        self.titledb = data
        self.logger.log(self.loc.getKey("msg_loadedTitledb", [titledb]))
        
    def getTitleNameFromId(self, titleid=None):
        if titleid == None:
            titleid = self.titleid
        for item in self.titledb:
            if titleid == item["id"]:
                return item["name"]
    
    def getUpdates(self):
        return self.Updates[self.titleid]
    
    def checkForUpdates(self, titleid):    
        #check given id
        check = False
        titleid = titleid.upper()
        for item in self.titledb:
            if titleid == item["id"]:
                check = True
                self.titleid = titleid
                self.logger.log(self.loc.getKey("msg_titleIDIs", [item["name"], item["id"]]))
                break
        if check == False:
            self.logger.log(self.loc.getKey("msg_titleIDNotValid"), "e")
            self.titleid = ""
            return
        
        #check for updates
        updates = []
        url = urllib.parse.urljoin(urllib.parse.urljoin("https://a0.ww.np.dl.playstation.net/tpl/np/", self.titleid+"/"), self.titleid+"-ver.xml")
        requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.SubjectAltNameWarning) 
        try:
            resp = requests.get(url, verify="sony.pem", proxies=self.proxies)
        except requests.exceptions.ConnectionError:
            self.logger.log(self.loc.getKey("msg_metaNotAvailable"), "e")
            if self.getConfig("use_proxy"):
                self.logger.log(self.loc.getKey("msg_checkProxySettings"))
            self.titleid = ""
            return
        
        info = resp.content
        #check file length for titles like BCAS20074
        if len(info) == 0:
            self.logger.log(self.loc.getKey("msg_metaFileEmpty"), "e")
            self.titleid = ""
            return
        root = ET.fromstring(info)
        if root.attrib["titleid"] == self.titleid:
            for tag in root:
                for package in tag:
                    pack = {}
                    attr = package.attrib
                    pack["gameid"] = self.titleid
                    pack["version"] = attr["version"]
                    pack["size"] = attr["size"]
                    pack["sha1"] = attr["sha1sum"]
                    pack["url"] = attr["url"]
                    pack["sysver"] = attr["ps3_system_ver"]
                    updates.append(pack)
        self.Updates[titleid] = updates
    
    def downloadFiles(self, window):
        self.logger.log(self.loc.getKey("msg_startingDownloads"))
        i = 1
        ql = len(self.DlList.queue)
        for dl in self.DlList.queue:
            skip = False
            url = dl["url"]
            sha1 = dl["sha1"]
            size = dl["size"]
            id = dl["gameid"]
            fdir = os.path.join(self.config["dldir"]+"/", utils.filterIllegalCharsFilename(self.getTitleNameFromId(id))+"["+id+"]/")
            fname = os.path.join(fdir, utils.filterIllegalCharsFilename(os.path.basename(url)))
            total, used, free = shutil.disk_usage(fdir)
            if os.path.exists(self.config["dldir"]) == False and os.path.isfile(self.config["dldir"]) == False:
                try:
                    os.mkdir(self.config["dldir"])
                except (PermissionError, FileNotFoundError):
                    self.logger.log(self.loc.getKey("msg_dldirNotWriteable", [self.config["dldir"]]))
                    skip = True
            if os.path.exists(fdir) == False and os.path.isfile(fdir) == False:
                try:
                    os.mkdir(fdir)
                except (PermissionError, FileNotFoundError):
                    self.logger.log(self.loc.getKey("msg_dldirNotWriteable", [self.config["dldir"]]))
                    skip = True

            if self.config["checkIfAlreadyDownloaded"] == True:
                #check if file already exists
                if os.path.exists(fname) and os.path.isfile(fname):
                    if int(os.path.getsize(fname)) == int(size):
                        if self.config["verify"] == False:
                            self.logger.log(self.loc.getKey("msg_alreadyDownloadedNoVerify", [os.path.basename(url)]))
                            skip = True
                        else:
                            if sha1 == self._sha1File(fname):
                                self.logger.log(self.loc.getKey("msg_alreadyDownloadedVerify", [os.path.basename(url)]))
                                skip = True
            if skip == False:
                if used / total * 100 <= self.getConfig("storageThreshold"):
                    if free > int(size):
                        self.logger.log(self.loc.getKey("msg_startSingleDownload", [i, ql]))
                        self._download_file(url, fname, size, window, i)
                        self.DlList.removeEntry(dl["gameid"]+"-"+dl["version"])
                    else:
                        self.logger.log(self.loc.getKey("msg_notEnoughDiskSpace"), "e")
                        skip = True
                else:
                    self.logger.log(self.loc.getKey("msg_spaceBelowThreshold", [self.getConfig("storageThreshold")]), "e")
                    skip = True
            if self.config["verify"] == True and skip == False:
                if sha1 == self._sha1File(fname):
                    self.logger.log(self.loc.getKey("msg_verifySuccess", [fname]))
                else:
                    self.logger.log(self.loc.getKey("msg_verifyFailure", [fname]))
                    os.remove(fname)
            if self.config["verify"] == False and skip == False:
                self.logger.log(self.loc.getKey("msg_noVerify", [fname]))
            i += 1
            
        self.logger.log(self.loc.getKey("msg_finishedDownload", [ql]))
    
    def _download_file(self, url, local_filename, size, window, num):
        text = window["window_main_progress_label"]
        bar = window["window_main_progress_bar"]
        size = int(size)
        chunk_size=8192
        count = 0
        already_loaded = 0
        with requests.get(url, stream=True, proxies=self.proxies) as r:
            r.raise_for_status()
            start = time.perf_counter()
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=chunk_size): 
                    if chunk:
                        f.write(chunk)
                        count += 1
                        already_loaded = count * chunk_size
                        if already_loaded / size > 1:
                            already_loaded = size
                        percentage = already_loaded / size * 100
                        text.Update(self.loc.getKey("window_main_progress_label", [num, utils.formatSize(already_loaded), utils.formatSize(size), format(float(percentage), '.1f'), utils.formatSize(already_loaded//(time.perf_counter() - start))+"s"]))
                        bar.UpdateBar(percentage)
                        window.Refresh()

    def _sha1File(self, fname):
        #copy file
        f2 = fname+"~"
        shutil.copy(fname, f2)
        with open(f2, "ab") as f:
            #remove last 32 bytes
            f.seek(-32, os.SEEK_END)
            f.truncate()
        fsha = hashlib.sha1()
        with open(f2, "rb") as f:
            for line in iter(lambda: f.read(fsha.block_size), b''):
                fsha.update(line)
        os.remove(f2)
        return fsha.hexdigest()
    
    def __del__(self):
        del self.logger

class Queue():
    def __init__(self):
        self.queue = []
    
    def addEntry(self, entry):
        if self.isAlreadInQueue(entry["gameid"]+"-"+entry["version"]) != True:
            self.queue.append({"num":(len(self.queue)+1), "code":entry["gameid"]+"-"+entry["version"], "gameid":entry["gameid"], "version":entry["version"], "size": entry["size"], "url": entry["url"], "sha1": entry["sha1"]})
    
    def removeEntry(self, code):
        newQueue = []
        for item in self.queue:
            if item["code"] != code:
                newQueue.append(item)
        self.queue = newQueue
        self._sortQueue()
    
    def _sortQueue(self):
        newQueue = []
        sort = {}
        for item in self.queue:
            sort[item["num"]] = item
        sort = dict(sorted(sort.items()))
        for key, value in sort.items():
            pack = value
            pack["num"] = key
            newQueue.append(pack)
        self.queue = newQueue
        
    def moveUp(self, code):
        before = False
        for item in self.queue:
            if item["code"] == code:
                currentNum = item["num"]
                before = True
            if before == False:
                newNum = item["num"]
                newCode = item["code"]
        if currentNum != 1:
            sort = {}
            for item in self.queue:
                sort[item["code"]] = item
            sort[code]["num"] = newNum
            sort[newCode]["num"] = currentNum
            newQueue = []
            for key, value in sort.items():
                newQueue.append(value)
            self.queue = newQueue
            self._sortQueue()
    
    def moveDown(self, code):
        after = False
        for item in self.queue:
            if after == True:
                newNum = item["num"]
                newCode = item["code"]
                after = False
            if item["code"] == code:
                currentNum = item["num"]
                after = True
        if currentNum != len(self.queue):
            sort = {}
            for item in self.queue:
                sort[item["code"]] = item
            sort[code]["num"] = newNum
            sort[newCode]["num"] = currentNum
            newQueue = []
            for key, value in sort.items():
                newQueue.append(value)
            self.queue = newQueue
            self._sortQueue()
        
    def getTotalDownloadSize(self):
        size = 0
        for item in self.queue:
            size += int(item["size"])
        return int(size)
        
    def isAlreadInQueue(self, code):
        ret = False
        for item in self.queue:
            if code == item["code"]:
                ret = True
        return ret