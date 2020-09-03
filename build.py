#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#
# build.py for PS3GameUpdateDownloader by shinrax2

#built-in
import argparse
import sys
import shutil
import os
import platform
import json
import contextlib
import logging

#pip packages
#import PyInstaller.__main__
import git

def buildheader(version, commitid, args, pyiver="None"):
    print("Building PS3GameUpdateDownloader")
    print("Version: "+version)
    print("Git Commit: "+commitid)
    print("Python version: "+sys.version)
    print("PyInstaller version: "+pyiver)
    print("Compiled: "+str(args.c))
    print("Debug: "+str(args.d))

#setup argparse
parser = argparse.ArgumentParser(description="buildscript for PS3GameUpdateDownloader")
parser.add_argument("-s", action="store_true", help="building a source version")
parser.add_argument("-c", action="store_true", help="building a compiled version")
parser.add_argument("-r", action="store_true", help="building a release version")
parser.add_argument("-d", action="store_true", help="building a debug version")
parser.add_argument("-z", action="store_true", help="pack the build to a .zip file")
args = parser.parse_args()

#constants
builddir = "dist/PS3GameUpdateDownloader"
suffix = ""
arch = ""
repo = git.Repo()
gitver = repo.head.object.hexsha
if platform.system() == "Windows":
    suffix = ".exe"
    arch += "win"
if platform.system() == "Linux":
    arch += "linux"
if platform.architecture()[0] == "32bit":
    arch += "32"
if platform.architecture()[0] == "64bit":
    arch += "64"
with open("release.json", "r", encoding="utf8") as f:
    version = json.loads(f.read())["version"]
#check parameters
action = ""
zip = False
if args.c == True and args.s == True:
    print("you cant pass \"-c\" and \"-s\" to the buildscript")
    sys.exit()
if args.d == True and args.r == True:
    print("you cant pass \"-d\" and \"-r\" to the buildscript")
    sys.exit()
if args.s == True and args.r == True:
    action = "sourcerelease"
if args.s == True and args.d == True:
    action = "sourcedebug"
if args.c == True and args.r == True:
    action = "compilerelease"
if args.c == True and args.d == True:
    action = "compiledebug"
if args.z == True:
    zip = True
    zipname = "dist/PS3GameUpdateDownloader-"+version

if action == "sourcerelease":
    #release running from source
    if os.path.exists(builddir):
        #delete old build
        shutil.rmtree(builddir)
        os.makedirs(builddir)
    else:
        os.makedirs(builddir)
    with open(os.path.join(builddir, "build.log"), "w") as f:
        with contextlib.redirect_stdout(f):
            buildheader(version, gitver, args)
           #copy scripts
            shutil.copy2("main.py", os.path.join(builddir, "main.py"))
            shutil.copy2("utils.py", os.path.join(builddir, "utils.py"))
            shutil.copy2("updater.py", os.path.join(builddir, "updater.py"))
            shutil.copy2("PS3GUD.py", os.path.join(builddir, "PS3GUD.py"))
            shutil.copy2("gui.py", os.path.join(builddir, "gui.py"))
            #copy data
            shutil.copy2("CHANGELOG", os.path.join(builddir, "CHANGELOG"))
            shutil.copy2("titledb.json", os.path.join(builddir, "titledb.json"))
            shutil.copy2("requirements.txt", os.path.join(builddir, "requirements.txt"))
            shutil.copy2("release.json", os.path.join(builddir, "release.json"))
            shutil.copy2("sony.pem", os.path.join(builddir, "sony.pem"))
            shutil.copytree("./loc", os.path.join(builddir, "loc"))
            
            #build zip
            if zip == True:
                shutil.make_archive(zipname+"-source", "zip", "dist", os.path.relpath(builddir, "dist"))
   
if action == "sourcedebug":
    #debug running from source
    builddir += "Debug"
    if os.path.exists(builddir):
        #delete old build
        shutil.rmtree(builddir)
        os.makedirs(builddir)
    else:
        os.makedirs(builddir)
    with open(os.path.join(builddir, "build.log"), "w") as f:
        with contextlib.redirect_stdout(f):
            buildheader(version, gitver, args)
            #copy scripts
            shutil.copy2("main.py", os.path.join(builddir, "main.py"))
            shutil.copy2("utils.py", os.path.join(builddir, "utils.py"))
            shutil.copy2("updater.py", os.path.join(builddir, "updater.py"))
            shutil.copy2("PS3GUD.py", os.path.join(builddir, "PS3GUD.py"))
            shutil.copy2("gui.py", os.path.join(builddir, "gui.py"))
            #copy data
            shutil.copy2("CHANGELOG", os.path.join(builddir, "CHANGELOG"))
            shutil.copy2("titledb.json", os.path.join(builddir, "titledb.json"))
            shutil.copy2("release.debug.json", os.path.join(builddir, "release.json"))
            shutil.copy2("requirements.txt", os.path.join(builddir, "requirements.txt"))
            shutil.copy2("sony.pem", os.path.join(builddir, "sony.pem"))
            shutil.copytree("./loc", os.path.join(builddir, "loc"))
            
            #build zip
            if zip == True:
                shutil.make_archive(zipname+"-source-debug", "zip", "dist", os.path.relpath(builddir, "dist"))
        
if action == "compilerelease":
    #compiled release
    #delete old build
    if os.path.exists(builddir):
        shutil.rmtree(builddir)
        os.makedirs(builddir)
    else:
        os.makedirs(builddir)
    with open(os.path.join(builddir, "build.log"), "w") as f:
        with contextlib.redirect_stdout(f):
            #build main executable
            import PyInstaller.__main__
            import PyInstaller.__init__
            buildheader(version, gitver, args, pyiver=PyInstaller.__init__.__version__)
            fh = logging.FileHandler(os.path.join(builddir, "build.log"))
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(logging.Formatter('%(relativeCreated)d %(levelname)s: %(message)s'))
            log = logging.getLogger("PyInstaller")
            log.addHandler(fh)
            PyInstaller.__main__.run([
                "--name=ps3gud",
                "--onefile",
                "--windowed",
                "main.py"
            ])
            #build updater executable
            PyInstaller.__main__.run([
                "--name=PS3GUDup",
                "--onefile",
                "--windowed",
                "updater.py"
            ])
            #move executables to buildir
            shutil.move("dist/ps3gud"+suffix, os.path.join(builddir, "ps3gud"+suffix))
            shutil.move("dist/PS3GUDup"+suffix, os.path.join(builddir, "PS3GUDup"+suffix))
            #copy data
            shutil.copy2("CHANGELOG", os.path.join(builddir, "CHANGELOG"))
            shutil.copy2("titledb.json", os.path.join(builddir, "titledb.json"))
            shutil.copy2("release.json", os.path.join(builddir, "release.json"))
            shutil.copy2("sony.pem", os.path.join(builddir, "sony.pem"))
            shutil.copytree("./loc", os.path.join(builddir, "loc"))
            
            #build zip
            if zip == True:
                shutil.make_archive(zipname+"-"+arch, "zip", "dist", os.path.relpath(builddir, "dist"))

if action == "compiledebug":
    #compiled debug
    builddir += "Debug"
    #delete old build
    if os.path.exists(builddir):
        shutil.rmtree(builddir)
        os.makedirs(builddir)
    else:
        os.makedirs(builddir)
    with open(os.path.join(builddir, "build.log"), "w") as f:
        with contextlib.redirect_stdout(f):
            #build main executable
            import PyInstaller.__main__
            import PyInstaller.__init__
            buildheader(version, gitver, args, pyiver=PyInstaller.__init__.__version__)
            fh = logging.FileHandler(os.path.join(builddir, "build.log"))
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(logging.Formatter('%(relativeCreated)d %(levelname)s: %(message)s'))
            log = logging.getLogger("PyInstaller")
            log.addHandler(fh)
            PyInstaller.__main__.run([
                "--name=ps3gud",
                "--onefile",
                "--windowed",
                "main.py"
            ])
            #build updater executable
            PyInstaller.__main__.run([
                "--name=PS3GUDup",
                "--onefile",
                "--windowed",
                "updater.py"
            ])
            #move executables to buildir
            shutil.move("dist/ps3gud"+suffix, os.path.join(builddir, "ps3gud"+suffix))
            shutil.move("dist/PS3GUDup"+suffix, os.path.join(builddir, "PS3GUDup"+suffix))
            #copy data
            shutil.copy2("CHANGELOG", os.path.join(builddir, "CHANGELOG"))
            shutil.copy2("titledb.json", os.path.join(builddir, "titledb.json"))
            shutil.copy2("release.debug.json", os.path.join(builddir, "release.json"))
            shutil.copy2("sony.pem", os.path.join(builddir, "sony.pem"))
            shutil.copytree("./loc", os.path.join(builddir, "loc"))
            
            #build zip
            if zip == True:
                shutil.make_archive(zipname+"-"+arch+"-debug", "zip", "dist", os.path.relpath(builddir, "dist"))