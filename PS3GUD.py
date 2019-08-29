#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#
# PS3GameUpdateDownloader by shinrax2

import argparse
import urllib.request
import ssl
import xml.etree.ElementTree as ET
import os
import hashlib
import requests
import sys

def download_file(url, local_filename):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192): 
                if chunk:
                    f.write(chunk)

pars = argparse.ArgumentParser(description="Downloads Updates for PS3 Games with given ID")
pars.add_argument("gameid", metavar="gameid", type=str, nargs=1, help="ID of a PS3 Game")

args = pars.parse_args()
if args.gameid[0] and args.gameid[0] != "" and type(args.gameid[0]) == str:
	#config
	dldir = "./downloadedPKGs/" #target dir for downloaded updates !!!END WITH TRAILING SLASH!!!
	verify = False #verify checksums of downloaded updates DOESNT WORK ATM
	checkIfAlreadyDownloaded = True #check if file already exists and size matches
	
	#load title db
	with open("titledb.txt", "r", encoding="utf8") as f:
		data = []
		for line in f:
			item = {}
			item["id"], item["name"] = line.split("\t\t")
			if item["name"].endswith("\n"):
				item["name"] = item["name"][:-1]
			data.append(item)
	titledb = data
	#check given id
	check = False
	for item in titledb:
		if args.gameid[0] == item["id"]:
			check = True
			gameid = args.gameid[0]
			print("Game is: "+item["name"])
			break
	if check == False:
		print("given gameid is not valid")
		sys.exit(0)
	
	#check for updates
	updates = []
	ssl._create_default_https_context = ssl._create_unverified_context # needed for sonys self signed cert
	url = "https://a0.ww.np.dl.playstation.net/tpl/np/"+gameid+"/"+gameid+"-ver.xml"
	try:
		resp = urllib.request.urlopen(url)
	except urllib.error.HTTPError:
		print("meta file for this gameid is not available")
		sys.exit(0)
	
	data = resp.read()
	info = data.decode('utf-8')
	#check file length for titles like BCAS20074
	if len(info) == 0:
		print("meta file for this gameid contains no info")
		sys.exit(0)
	root = ET.fromstring(info)
	if root.attrib["titleid"] == gameid:
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
	#ask user which to download
	if len(updates)>0:
		i = 1
		dllist = []
		print("updates found!\n")
		for pack in updates:
			print("package: "+str(i))
			print("version: "+pack["version"])
			print("size: "+str(format(float(pack["size"])/1024/1024, '.2f'))+"MB")
			print("requires ps3 firmware version: "+pack["sysver"]+"\n")
			i += 1
		while True:
			re = input("which package you want to download? enter package number or all: ")
			if re.isdigit() == True:
				if int(re) < len(updates) and int(re) > 0:
					re = int(re) - 1
					dllist.append(re)
					break
				else:
					print("please enter a correct number or all")
			elif re == "all":
				for ii in range(0, len(updates)):
					dllist.append(ii)
				break
			else:
				print("please enter a correct number or all")
		print("starting download of package(s)")
		i = 1
		for dl in dllist:
			print("starting download "+str(i)+" of "+str(len(dllist)))
			url = updates[dl]["url"]
			sha1 = updates[dl]["sha1"]
			size = updates[dl]["size"]
			fname = dldir+os.path.basename(url)
			skip = False
			if checkIfAlreadyDownloaded == True:
				#check if file already exists
				if os.path.exists(fname) and os.path.isfile(fname):
					if os.path.getsize(fname) == size:
						print("file '"+os.path.basename(url)+"' was already downloaded! skipping it!")
						skip = True
			if skip == False:
				download_file(url, fname)
			if verify == True:
				fsha = hashlib.sha1()
				with open(fname, "rb") as f:
					for line in iter(lambda: f.read(65536), b''):
						fsha.update(line)
				if sha1 == fsha.hexdigest():
					print('"'+fname+'" successfully verified')
				else:
					print('verification of "'+fname+'" failed')
			if verify == False:
				print("not verifying file!")
			i += 1
		
		print("finished downloading "+str(len(dllist))+" files!")
	else:
		print("no updates for this title found!")
		
input("please press enter to exit")
