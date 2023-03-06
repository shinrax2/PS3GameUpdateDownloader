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
import platform
import ssl

#local files
import utils

#pip packages
import requests
import requests.adapters
import keyring

class PS3GUD():
    def __init__(self, window=None):
        if window != None:
            self.logger = utils.Logger(window)
        else:
            self.logger = utils.Logger()
        self.configFile = "./config.json"
        self.titledbFile = "./titledb.json"
        self.config = {}
        self.Updates = {}
        self.DlList = Queue(self)
        self.titleid = ""
        self.proxies = {}
        #handle sonys weak cert for their https server
        self.https_session = requests.Session()
        self.https_session.mount('https://a0.ww.np.dl.playstation.net', SonySSLContextAdapter())
        
        self.useDefaultConfig = True
        self.configDefaults = {}
        self.configDefaults["dldir"] = "./downloadedPKGs"
        self.configDefaults["verify"] = True
        self.configDefaults["checkIfAlreadyDownloaded"] = True
        self.configDefaults["storageThresholdNew"] = 5
        self.configDefaults["currentLoc"] = "en"
        self.configDefaults["checkForNewRelease"] = True
        self.configDefaults["use_proxy"] = False
        self.configDefaults["proxy_ip"] = ""
        self.configDefaults["proxy_port"] = ""
        self.configDefaults["proxy_user"] = None
        self.configDefaults["proxy_pass"] = None
        self.configDefaults["dont_show_again_keyring_support"] = False
        self.configDefaults["rename_pkgs"] = True
        self.configDefaults["update_titledb"] = True
        
    def setWindow(self, window):
        self.logger.window = window
        
    def setLoc(self, loc):
        self.loc = loc

    def logHeader(self, version, psgversion, commit):
        self.logger.log(f"PS3GameUpdateDownloader {version}")
        self.logger.log(f"Git Commit: {commit}")
        self.logger.log(f"Config File: {self.configFile}")
        self.logger.log(f"Language: {self.loc.getLoc()}")
        self.logger.log(f"Current working directory: {os.getcwd()}")
        self.logger.log(f"Compiled: {str(utils.isAppFrozen())}")
        self.logger.log(f"PySimpleGUI version: {psgversion}")
        self.logger.log(f"Python version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}{sys.version_info.releaselevel} ({platform.python_implementation()})\n")
        
    def loadConfig(self):
        if os.path.exists(self.configFile) and os.path.isfile(self.configFile):
            self.logger.log(self.loc.getKey("msg_configFileLoaded"))
            with open(self.configFile, "r", encoding="utf8") as f:
                data = f.read()
            try:
                self.config = json.loads(data)
            except json.decoder.JSONDecodeError:
                self.logger.log(self.loc.getKey("msg_ConfigFileCorrupt"), "e")
                os.remove("./config.json")
                self.config = self.configDefaults
                return
            self.useDefaultConfig = False
            if self.getConfig("use_proxy") == True:
                self.config["proxy_pass"], self.config["proxy_user"] = self.getProxyCredentials()
            else:
                self.config["proxy_pass"], self.config["proxy_user"] = (None, None)
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
        
    def setProxyCredentials(self, pwd, user):
        keyring.set_password("ps3gud", "proxy_pass", pwd)
        self.config["proxy_pass"] = pwd
        keyring.set_password("ps3gud", "proxy_user", user)
        self.config["proxy_user"] = user
        
    def getProxyCredentials(self):
        return (keyring.get_password("ps3gud", "proxy_pass"), keyring.get_password("ps3gud", "proxy_user"))
        
    def setupProxy(self):
        if self.getConfig("use_proxy") and self.getConfig("proxy_ip") != "" and self.getConfig("proxy_port") != "":
            self.proxies["http"] = "socks5://"
            self.proxies["https"] = "socks5://"
            if self.getConfig("proxy_user") != None:
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
    
    def checkTitleDbVersion(self):
        if self.getConfig("update_titledb") == True:
            file = "https://raw.githubusercontent.com/shinrax2/PS3GameUpdateDownloader/master/titledb.json"
            meta = "https://raw.githubusercontent.com/shinrax2/PS3GameUpdateDownloader/master/release.json"
            try:
                data = json.loads(requests.get(meta, proxies=self.proxies).content)
            except requests.exceptions.ConnectionError:
                if self.getConfig("use_proxy"):
                    self.logger.log(self.loc.getKey("msg_checkProxySettings"))
                return
            
            if self.titledbver < data["tdb_version"]:
                self.logger.log(self.loc.getKey("msg_newTitleDbVersion"))
                if os.path.exists(self.titledbFile+".bak"):
                    os.remove(self.titledbFile+".bak")
                os.rename(self.titledbFile, self.titledbFile+".bak")
                try:
                    newtdb = json.loads(requests.get(file, proxies=self.proxies).content)
                except requests.exceptions.ConnectionError:
                    if self.getConfig("use_proxy"):
                        self.logger.log(self.loc.getKey("msg_checkProxySettings"))
                    return
                with open(self.titledbFile, "w", encoding="utf8") as f:
                    f.write(json.dumps(newtdb, ensure_ascii=False))
                    f.flush()
                self.loadTitleDb()
        
    
    def loadTitleDb(self):
        with open(self.titledbFile, "r", encoding="utf8") as f:
            data = json.loads(f.read())
        self.titledb = data["db"]
        self.titledbver = data["version"]
        self.logger.log(self.loc.getKey("msg_loadedTitledb", [self.titledbFile]))
        
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
        try:
            resp = self.https_session.get(url, verify="sony.pem", proxies=self.proxies)
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
        try:
            root = ET.fromstring(info)
        except ET.ParseError:
            self.logger.log(self.loc.getKey("msg_metaFileBrokenSyntax", [self.titleid]), "e")
            self.titleid = ""
            return
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
            fdir = os.path.join(self.getConfig("dldir")+"/", utils.filterIllegalCharsFilename(self.getTitleNameFromId(id))+"["+id+"]/")
            if self.getConfig("rename_pkgs") == True:
                fname = os.path.join(fdir, utils.filterIllegalCharsFilename(self.getTitleNameFromId(id)+"_["+id+"]_"+dl["version"]+".pkg"))
            else:
                fname = os.path.join(fdir, utils.filterIllegalCharsFilename(os.path.basename(url)))

            if os.path.exists(self.getConfig("dldir")) == False and os.path.isfile(self.getConfig("dldir")) == False:
                try:
                    os.mkdir(self.getConfig("dldir"))
                except (PermissionError, FileNotFoundError):
                    self.logger.log(self.loc.getKey("msg_dldirNotWriteable", [self.getConfig("dldir")]))
                    skip = True
            if os.path.exists(fdir) == False and os.path.isfile(fdir) == False:
                try:
                    os.mkdir(fdir)
                except (PermissionError, FileNotFoundError):
                    self.logger.log(self.loc.getKey("msg_dldirNotWriteable", [self.getConfig("dldir")]))
                    skip = True
            total, used, free = shutil.disk_usage(fdir)
            
            if self.getConfig("checkIfAlreadyDownloaded") == True:
                #check if file already exists
                if os.path.exists(fname) and os.path.isfile(fname):
                    if int(os.path.getsize(fname)) == int(size):
                        if self.getConfig("verify") == False:
                            self.logger.log(self.loc.getKey("msg_alreadyDownloadedNoVerify", [os.path.basename(url)]))
                            skip = True
                        else:
                            if sha1 == self._sha1File(fname):
                                self.logger.log(self.loc.getKey("msg_alreadyDownloadedVerify", [os.path.basename(url)]))
                                skip = True
            if skip == False:
                if free >= int(self.getConfig("storageThresholdNew"))*1024*1024*1024:
                    if free > int(size):
                        self.logger.log(self.loc.getKey("msg_startSingleDownload", [i, ql]))
                        self._download_file(url, fname, size, window, i)
                        self.DlList.removeEntry(dl["gameid"]+"-"+dl["version"])
                    else:
                        self.logger.log(self.loc.getKey("msg_notEnoughDiskSpace"), "e")
                        skip = True
                else:
                    self.logger.log(self.loc.getKey("msg_spaceBelowThreshold", [str(self.getConfig("storageThresholdNew"))+"GiB"]), "e")
                    skip = True
            if self.getConfig("verify") == True and skip == False:
                if sha1 == self._sha1File(fname):
                    self.logger.log(self.loc.getKey("msg_verifySuccess", [fname]))
                else:
                    self.logger.log(self.loc.getKey("msg_verifyFailure", [fname]))
                    os.remove(fname)
            if self.getConfig("verify") == False and skip == False:
                self.logger.log(self.loc.getKey("msg_noVerify", [fname]))
            if skip == True:
                self.DlList.removeEntry(dl["gameid"]+"-"+dl["version"])
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
                        text.Update(self.loc.getKey("window_main_progress_label", [num, utils.formatSize(already_loaded), utils.formatSize(size), format(float(percentage), '.1f'), utils.formatSize(already_loaded//(time.perf_counter() - start))+"/s"]))
                        bar.UpdateBar(percentage)
                        window.Refresh()

    def _sha1File(self, fname):
        # get hash from EOF
        with open(fname, "rb") as f:
            fhash = f.read()[-32:].hex()[:40]
        #copy file
        f2 = fname+"~"
        shutil.copy(fname, f2)
        #remove last 32 bytes because the PKG hash is at EOF and not part of the PKG data
        with open(f2, "ab") as f:
            f.seek(-32, os.SEEK_END)
            f.truncate()
        #calculate hash from file - last 32 bytes
        fsha = hashlib.sha1()
        with open(f2, "rb") as f:
            for line in iter(lambda: f.read(fsha.block_size), b''):
                fsha.update(line)
        os.remove(f2)
        #check calculated hash against EOF hash
        if fhash == fsha.hexdigest():
            #return correct hash
            return fsha.hexdigest()
        else:
            #return fake hash
            return "DEADBEEFDEADBEEFDEADBEEFDEADBEEFDEADBEEF"
    
    def __del__(self):
        del self.logger

class Queue():
    def __init__(self, ps3):
        self.queue = []
        self.ps3 = ps3
    
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
        
    def exportQueue(self, exportFile):
        s = ""
        games = {}
        for entry in self.queue:
            try:
                games[entry["gameid"]]
            except KeyError:
                games[entry["gameid"]] = []
            games[entry["gameid"]].append(entry["url"])
        for id, data in games.items():
            s += self.ps3.getTitleNameFromId(id)+"["+id+"]:\n\n"
            for url in data:
                s += "\t"+url+"\n"
            s += "\n"
        with open(exportFile, "w", encoding="utf8") as f:
            f.write(s)

class SonySSLContextAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = ssl.create_default_context()
        context.set_ciphers('DEFAULT:@SECLEVEL=1')
        kwargs['ssl_context'] = context
        return super(SonySSLContextAdapter, self).init_poolmanager(*args, **kwargs)
