#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#
# PS3GameUpdateDownloader by shinrax2

#built-in
import urllib.request
import ssl
import xml.etree.ElementTree as ET
import os
import hashlib
import sys
import shutil

#pip
import requests

#local files
import utils

class PS3GUD():
    def __init__(self, window=None):
        self.logger = utils.Logger("log.txt", window)
        self.Updates = {}
        self.DlList = []
        self.titleid = ""
        
    def setConfig(self, dldir="./downloadedPKGs", verify=True, checkIfAlreadyDownloaded=True, storageThreshold=95):
        if os.path.exists(dldir) == False:
            os.mkdir(dldir)
        self.dldir = dldir
        self.verify = verify
        self.checkIfAlreadyDownloaded = checkIfAlreadyDownloaded
        self.storageThreshold = storageThreshold
    
    def loadTitleDb(self, titledb = "titledb.txt"):
        with open(titledb, "r", encoding="utf8") as f:
            data = []
            for line in f:
                item = {}
                item["id"], item["name"] = line.split("\t\t")
                if item["name"].endswith("\n"):
                    item["name"] = item["name"][:-1]
                data.append(item)
        self.titledb = data
        self.logger.log("title db loaded from: "+titledb)
        
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
        for item in self.titledb:
            if titleid == item["id"]:
                check = True
                self.titleid = titleid
                self.logger.log("Game is: "+item["name"]+"\t titleid: "+item["id"])
                break
        if check == False:
            self.logger.log("given gameid is not valid", "e")
            self.titleid = ""
            return
        
        #check for updates
        updates = []
        ssl._create_default_https_context = ssl._create_unverified_context # needed for sonys self signed cert
        url = "https://a0.ww.np.dl.playstation.net/tpl/np/"+self.titleid+"/"+self.titleid+"-ver.xml"
        try:
            resp = urllib.request.urlopen(url)
        except urllib.error.HTTPError:
            self.logger.log("meta file for this gameid is not available", "e")
            self.titleid = ""
            return
        
        data = resp.read()
        info = data.decode('utf-8')
        #check file length for titles like BCAS20074
        if len(info) == 0:
            self.logger.log("meta file for this gameid contains no info", "e")
            self.titleid = ""
            return
        root = ET.fromstring(info)
        if root.attrib["titleid"] == self.titleid:
            for tag in root:
                for package in tag:
                    pack = {}
                    attr = package.attrib
                    pack["version"] = attr["version"]
                    pack["size"] = attr["size"]
                    pack["sha1"] = attr["sha1sum"]
                    pack["url"] = attr["url"]
                    pack["sysver"] = attr["ps3_system_ver"]
                    updates.append(pack)
        self.Updates[titleid] = updates
    
    def askWhichToDownload(self):
        if len(self.Updates[self.titleid])>0:
            i = 1
            dllist = []
            print("updates found!\n")
            for pack in self.Updates[self.titleid]:
                print("package: "+str(i))
                print("version: "+pack["version"])
                print("size: "+utils.formatSize(pack["size"]))
                print("requires ps3 firmware version: "+pack["sysver"]+"\n")
                i += 1
            while True:
                re = input("which package you want to download? enter package number or all: ")
                if re.isdigit() == True:
                    if int(re) < (len(self.Updates[self.titleid])+1) and int(re) > 0:
                        re = int(re) - 1
                        self.DlList.append(self.Updates[self.titleid][re])
                        break
                    else:
                        print("please enter a correct number or all")
                elif re == "all":
                    for ii in range(0, len(self.Updates[self.titleid])):
                        self.DlList.append(self.Updates[self.titleid][ii])
                    break
                else:
                    print("please enter a correct number or all")
    
    def downloadFiles(self):
        self.logger.log("starting download of package(s)")
        i = 1
        for dl in self.DlList:
            url = dl["url"]
            sha1 = dl["sha1"]
            size = dl["size"]
            fdir = self.dldir+"/"+utils.filterIllegalCharsFilename(self.getTitleNameFromId())+"["+self.titleid+"]/"
            fname = fdir+utils.filterIllegalCharsFilename(os.path.basename(url))
            if os.path.exists(fdir) == False and os.path.isfile(fdir) == False:
                os.mkdir(fdir)
            skip = False
            if self.checkIfAlreadyDownloaded == True:
                #check if file already exists
                if os.path.exists(fname) and os.path.isfile(fname):
                    if int(os.path.getsize(fname)) == int(size):
                        if self.verify == False:
                            self.logger.log("file '"+os.path.basename(url)+"' was already downloaded! skipping it! not verified!")
                            skip = True
                        else:
                            if sha1 == self._sha1File(fname):
                                self.logger.log("file '"+os.path.basename(url)+"' was already downloaded! skipping it! sha1 verified!")
                                skip = True
            if skip == False:
                self.logger.log("starting download "+str(i)+" of "+str(len(self.DlList)))
                self._download_file(url, fname, size)
            if self.verify == True:
                if sha1 == self._sha1File(fname):
                    self.logger.log('"'+fname+'" successfully verified')
                else:
                    self.logger.log('verification of "'+fname+'" failed\ndeleting file')
                    os.remove(fname)
            if self.verify == False:
                self.logger.log("not verifying file!")
            i += 1
            
        self.logger.log("finished downloading "+str(len(self.DlList))+" files!")
        self.DlList = []
    
    def _download_file(self, url, local_filename, size):
        total, used, free = shutil.disk_usage(os.path.dirname(local_filename))
        if used / total * 100 <= self.storageThreshold:
            if free > int(size):
                with requests.get(url, stream=True) as r:
                    r.raise_for_status()
                    with open(local_filename, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192): 
                            if chunk:
                                f.write(chunk)
            else:
                self.logger.log("not enought free disk space!", "e")
        else:
            self.logger.log("free disk space is below "+str(100-self.storageThreshold)+"%", "w")

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
        
if __name__ == "__main__":
    import argparse
    pars = argparse.ArgumentParser(description="Downloads Updates for PS3 Games with given ID")
    pars.add_argument("gameid", metavar="gameid", type=str, nargs=1, help="ID of a PS3 Game")

    args = pars.parse_args()
    if args.gameid[0] and args.gameid[0] != "" and type(args.gameid[0]) == str:
        ps3gud = PS3GUD()
        #config
        dldir = "./downloadedPKGs" #target dir for downloaded updates !!!END WITHOUT TRAILING SLASH!!!
        verify = True #verify checksums of downloaded updates
        checkIfAlreadyDownloaded = True #check if file already exists and size matches
        ps3gud.setConfig(dldir, verify, checkIfAlreadyDownloaded)
        #load title db
        ps3gud.loadTitleDb()
        ps3gud.checkForUpdates(args.gameid[0].upper())
        ps3gud.askWhichToDownload()
        ps3gud.downloadFiles()
        del ps3gud
    input("please press enter to exit")
