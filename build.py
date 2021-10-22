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
import logging

def buildheader(version, commitid , filepath , pyiver="None"):
    lines = [   "Building PS3GameUpdateDownloader",
                "Build script arguments: "+str(sys.argv[1:]),
                "Version: "+version,
                "Git Commit: "+commitid
            ]
    if pyiver != "None":
        lines.append("Python version: "+sys.version)
        lines.append("PyInstaller version: "+pyiver)
        lines.append("Platform: "+platform.system()+" "+platform.architecture()[0])
        lines.append("")
        lines.append("PyInstaller Output:")
        lines.append("")
    with Prepender(filepath) as filehandle:
        filehandle.write_lines(lines)

class Upx():
    def __init__(self, build_config="build_config.json"):
        self.upx  = {}
        self.build_config = build_config
        if os.path.isfile(self.build_config):
            with open(self.build_config, "r", encoding="utf8") as f:
                self.upx = json.loads(f.read())

    def get_upx_dir(self, arch=("win" if platform.system() == "Windows" else "linux")+("64" if platform.architecture()[0] == "64bit" else "32")):
        try:
            return self.upx[arch]
        except KeyError:
            self.ask_for_uxp_path(arch)
            return self.upx[arch]
    
    def ask_for_uxp_path(self, arch):
        check = False
        while check == False:
            upx = input("Please enter the path to your UPX("+arch+" version) installation:")
            if os.path.isdir(upx):
                check = True
                self.upx[arch] = os.path.abspath(upx)
                self.save_upx_paths()
            else:
                print("Please enter a valid path like C:\\upx-win32\\ or /opt/upx-i386-linux/ .")
    
    def save_upx_paths(self):
        if len(self.upx) > 0:
            print("Saving UPX paths to \""+self.build_config+"\"")
            with open(self.build_config, "w", encoding="utf8") as f:
                f.write(json.dumps(self.upx, sort_keys=True, indent=4, ensure_ascii=False))

# START from https://stackoverflow.com/questions/2677617/write-at-beginning-of-file/20805898#20805898 START
class Prepender(object):
    def __init__(self,
                 file_path,
                ):
        # Read in the existing file, so we can write it back later
        with open(file_path, mode='r') as f:
            self.__write_queue = f.readlines()

        self.__open_file = open(file_path, mode='w')

    def write_line(self, line): # line order is reversed
        self.__write_queue.insert(0,
                                  "%s\n" % line,
                                 )

    def write_lines(self, lines): # line order is maintained
        lines.reverse()
        for line in lines:
            self.write_line(line)

    def close(self):
        self.__exit__(None, None, None)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if self.__write_queue:
            self.__open_file.writelines(self.__write_queue)
        self.__open_file.close()
# END from https://stackoverflow.com/questions/2677617/write-at-beginning-of-file/20805898#20805898 END

#setup argparse
parser = argparse.ArgumentParser(description="buildscript for PS3GameUpdateDownloader")
parser.add_argument("-s", action="store_true", help="building a source version")
parser.add_argument("-c", action="store_true", help="building a compiled version")
parser.add_argument("-r", action="store_true", help="building a release version")
parser.add_argument("-d", action="store_true", help="building a debug version")
parser.add_argument("-z", action="store_true", help="pack the build to a .zip file")
parser.add_argument("-upx", action="store_true", help="use UPX to shrink executables")
parser.add_argument("-nogit", action="store_true", help="dont use git in the buildscript")
args = parser.parse_args()

#constants
builddir = "dist/PS3GameUpdateDownloader"
buildlog = os.path.join(builddir, "build.log")
suffix = ""
if platform.system() == "Windows":
    suffix = ".exe"
    ostype = "win"
if platform.system() == "Linux":
    ostype = "linux"
if platform.architecture()[0] == "32bit":
    bits = "32"
if platform.architecture()[0] == "64bit":
    bits = "64"
arch = ostype + bits
iconpath = os.path.abspath(os.path.join("images", "icon.ico"))

with open("release.json", "r", encoding="utf8") as f:
    version = json.loads(f.read())["version"]

#check parameters
action = ""
zip_check = False
upx_check = False
if args.c == True and args.s == True:
    print("You cant pass \"-c\" and \"-s\" to the buildscript.")
    sys.exit()
if args.d == True and args.r == True:
    print("You cant pass \"-d\" and \"-r\" to the buildscript.")
    sys.exit()
if args.c == False and args.upx == True:
    print("You need to build a compiled release to use UPX")
    sys.exit()
if args.s == True and args.r == True:
    action = "sourcerelease"
if args.s == True and args.d == True:
    action = "sourcedebug"
if args.c == True and args.r == True:
    action = "compilerelease"
if args.c == True and args.d == True:
    action = "compiledebug"
if args.c == True and args.upx == True:
    # setting up UPX
    upx_check = True
    upx_paths = Upx()
if args.z == True:
    zip_check = True
    zipname = "dist/PS3GameUpdateDownloader-"+version
if args.nogit == True:
    gitver = "None"
else:
    import git
    repo = git.Repo()
    gitver = repo.head.object.hexsha

if action == "sourcerelease":
    #release running from source
    if os.path.exists(builddir):
        #delete old build
        shutil.rmtree(builddir)
        os.makedirs(builddir)
    else:
        os.makedirs(builddir)
    with open(buildlog, "w") as f:
        #write header to buildlog
        buildheader(version, gitver, buildlog)
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
        shutil.copytree("./images", os.path.join(builddir, "images"))
        #build zip
        if zip_check == True:
            shutil.make_archive(zipname+"-source", "zip", "dist", os.path.relpath(builddir, "dist"))
   
if action == "sourcedebug":
    #debug running from source
    builddir += "Debug"
    buildlog = os.path.join(builddir, "build.log")
    if os.path.exists(builddir):
        #delete old build
        shutil.rmtree(builddir)
        os.makedirs(builddir)
    else:
        os.makedirs(builddir)
    with open(buildlog, "w") as f:
        #write header to buildlog
        buildheader(version, gitver, buildlog)
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
        shutil.copytree("./images", os.path.join(builddir, "images"))
        #build zip
        if zipzip_check == True:
            shutil.make_archive(zipname+"-source-debug", "zip", "dist", os.path.relpath(builddir, "dist"))
        
if action == "compilerelease":
    #compiled release
    #delete old build
    if os.path.exists(builddir):
        shutil.rmtree(builddir)
        os.makedirs(builddir)
    else:
        os.makedirs(builddir)
    #build main executable
    import PyInstaller.__main__
    import PyInstaller.__init__
    fh = logging.FileHandler(buildlog)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter('%(relativeCreated)d %(levelname)s: %(message)s'))
    log = logging.getLogger("PyInstaller")
    log.addHandler(fh)
    arg_main = [
        "--name=ps3gud",
        "--clean",
        "--onefile",
        "--windowed",
        "--icon="+iconpath
    ]
    if upx_check == True:
        arg_main.append("--upx-dir="+upx_paths.get_upx_dir())
        if platform.system() == "Windows": # fix for UPX
            arg_main.append("--upx-exclude=vcruntime140.dll")
    arg_main.append("main.py")
    PyInstaller.__main__.run(arg_main)
    #build updater executable
    arg_updater = [
        "--name=PS3GUDup",
        "--clean",
        "--onefile",
        "--windowed",
        "--icon=NONE"
    ]
    if upx_check == True:
        arg_updater.append("--upx-dir="+upx_paths.get_upx_dir())
        if platform.system() == "Windows": # fix for UPX
            arg_updater.append("--upx-exclude=vcruntime140.dll")
    arg_updater.append("updater.py")
    PyInstaller.__main__.run(arg_updater)
    #move executables to buildir
    shutil.move("dist/ps3gud"+suffix, os.path.join(builddir, "ps3gud"+suffix))
    shutil.move("dist/PS3GUDup"+suffix, os.path.join(builddir, "PS3GUDup"+suffix))
    #copy data
    shutil.copy2("CHANGELOG", os.path.join(builddir, "CHANGELOG"))
    shutil.copy2("titledb.json", os.path.join(builddir, "titledb.json"))
    shutil.copy2("release.json", os.path.join(builddir, "release.json"))
    shutil.copy2("sony.pem", os.path.join(builddir, "sony.pem"))
    shutil.copytree("./loc", os.path.join(builddir, "loc"))
    shutil.copytree("./images", os.path.join(builddir, "images"))
    #write header to buildlog
    buildheader(version, gitver, buildlog, pyiver=PyInstaller.__init__.__version__)
    #build zip
    if zip_check == True:
        shutil.make_archive(zipname+"-"+arch, "zip", "dist", os.path.relpath(builddir, "dist"))

if action == "compiledebug":
    #compiled debug
    builddir += "Debug"
    buildlog = os.path.join(builddir, "build.log")
    #delete old build
    if os.path.exists(builddir):
        shutil.rmtree(builddir)
        os.makedirs(builddir)
    else:
        os.makedirs(builddir)
    with open(buildlog, "w") as f:
        #build main executable
        import PyInstaller.__main__
        import PyInstaller.__init__
        fh = logging.FileHandler(os.path.join(builddir, "build.log"))
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter('%(relativeCreated)d %(levelname)s: %(message)s'))
        log = logging.getLogger("PyInstaller")
        log.addHandler(fh)
        arg_main = [
            "--name=ps3gud",
            "--clean",
            "--onefile",
            "--windowed",
            "--icon="+iconpath
        ]
        if upx_check == True:
            arg_main.append("--upx-dir="+upx_paths.get_upx_dir())
            if platform.system() == "Windows": # fix for UPX
                arg_main.append("--upx-exclude=vcruntime140.dll")
        arg_main.append("main.py")
        PyInstaller.__main__.run(arg_main)
        #build updater executable
        arg_updater = [
            "--name=PS3GUDup",
            "--clean",
            "--onefile",
            "--windowed",
            "--icon=NONE"
        ]
        if upx_check == True:
            arg_updater.append("--upx-dir="+upx_paths.get_upx_dir())
            if platform.system() == "Windows": # fix for UPX
                arg_updater.append("--upx-exclude=vcruntime140.dll")
        arg_updater.append("updater.py") 
        PyInstaller.__main__.run(arg_updater)
        #move executables to buildir
        shutil.move("dist/ps3gud"+suffix, os.path.join(builddir, "ps3gud"+suffix))
        shutil.move("dist/PS3GUDup"+suffix, os.path.join(builddir, "PS3GUDup"+suffix))
        #copy data
        shutil.copy2("CHANGELOG", os.path.join(builddir, "CHANGELOG"))
        shutil.copy2("titledb.json", os.path.join(builddir, "titledb.json"))
        shutil.copy2("release.debug.json", os.path.join(builddir, "release.json"))
        shutil.copy2("sony.pem", os.path.join(builddir, "sony.pem"))
        shutil.copytree("./loc", os.path.join(builddir, "loc"))
        shutil.copytree("./images", os.path.join(builddir, "images"))
        #write header to buildlog
        buildheader(version, gitver, buildlog, pyiver=PyInstaller.__init__.__version__)
        #build zip
        if zip_check == True:
            shutil.make_archive(zipname+"-"+arch+"-debug", "zip", "dist", os.path.relpath(builddir, "dist"))
