#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#
#PS3GameUpdateDownloader downloads PS3 game updates from official Sony servers
#Copyright (C) 2023 shinrax2
#
#This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
#This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.

#built-in
import argparse
import sys
import shutil
import os
import platform
import json
import logging
import subprocess
import datetime
import shlex
import stat

#local files
import utils

def buildheader(release, filepath , pyiver="None", winever=None):
    lines = [   "Building PS3GameUpdateDownloader",
                "Build script arguments: "+str(sys.argv[1:]),
                "Version: "+release["version"],
                "Git Commit: "+str(release["commitid"]),
                "Date/Time: "+str(NOW)
            ]
    if pyiver != "None":
        lines.append(f"Python version: Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}{sys.version_info.releaselevel} ({platform.python_implementation()})")
        lines.append(f"Platform: {platform.system()} {platform.architecture()[0]}")
        if platform.system() == "Windows" and winever is not None:
            lines.append(f"Built on Wine Version: {winever}")
        elif platform.system() == "Linux":
            lines.append(f"LibC: {platform.libc_ver()[0]} {platform.libc_ver()[1]}")
        lines.append(f"PyInstaller version: {pyiver}")
        lines.append("PyInstaller Output:")
    with Prepender(filepath) as filehandle:
        filehandle.write_lines(lines)

def createDigest(file):
    with open(file+".sha256", "w") as f:
        digest = utils.sha256File(file)
        f.write(digest)
        return digest

def validateJSON(filename):
    try:
        with open(filename, "r", encoding="utf8") as f:
            data = json.loads(f.read())
    except ValueError as err:
        print("\n\nJSON syntax error in \""+os.path.basename(filename)+"\"")
        print(err)
        input("Press enter to exit.")
        sys.exit(0)
    return data

def minifyJSON(jsonfiles):
    for file in jsonfiles:
        if file.endswith(".json") == True:
            data = validateJSON(file)
            with open(file, "w", encoding="utf8") as f:
                if os.path.basename(os.path.dirname(file)) == locdirname:
                    #if json file is a loc file remove comments
                    new_data = {}
                    for k, v in data.items():
                        new_data[k] = {"string": v["string"]}
                        data = new_data
                f.write(json.dumps(data, sort_keys=True, ensure_ascii=False))

def getJSONFiles():
    #list json files
    #loc files
    jsonfiles =  []
    for root, dirs, files in os.walk(locdirbuildpath):
        for file in files:
            if os.path.isfile(os.path.join(root, file)) and os.path.join(root, file).lower().endswith(".json"):
                jsonfiles.append(os.path.join(root, file))
    #other files
    jsonfiles.append(os.path.join(builddir, "release.json"))
    jsonfiles.append(os.path.join(builddir, "titledb.json"))
    return jsonfiles

def copyData(builddir, locdirname, imagedirname, debug=False, source=False):
    if debug == True: #debug specific files
        shutil.copy2("titledb.debug.json", os.path.join(builddir, "titledb.json"))
        shutil.copy2("release.debug.json", os.path.join(builddir, "release.json"))
    else: #release specific files
        shutil.copy2("LICENSE", os.path.join(builddir, "LICENSE"))
        shutil.copy2("CHANGELOG", os.path.join(builddir, "CHANGELOG"))
        shutil.copy2("release.json", os.path.join(builddir, "release.json"))
        shutil.copy2("titledb.json", os.path.join(builddir, "titledb.json"))
        copySource(builddir)
    if source == True: # source specific files
        shutil.copy2("requirements.txt", os.path.join(builddir, "requirements.txt"))
    # general files
    shutil.copy2("sony.pem", os.path.join(builddir, "sony.pem"))
    shutil.copytree(locdirname, os.path.join(builddir, locdirname))
    shutil.copytree(imagedirname, os.path.join(builddir, imagedirname), ignore=shutil.ignore_patterns("*.xcf"))

def copySource(builddir):
    sourcedir = os.path.join(builddir, "src")
    files = ["build.py", "buildrequirements.txt", "CHANGELOG", "gui.py", "LICENSE", "main_ps3gud.py", "missingstrings.py", "PS3GUD.py", "README.md", "release.debug.json", "release.debug.json", "release.json", "requirements.txt", "sony.pem", "titledb.json", "titledb.debug.json", "updater.py", "utils.py", "docker-build.sh", ".gitignore", ".gitattributes"]
    dirs = {
        "images": {
            "ignore": []
        },
        "loc": {
            "ignore": []
        },
        "dockerfiles": {
            "ignore": []
        },
        ".git": {
            "ignore": []
        },
        ".github": {
            "ignore": []
        },
    }
    #copy files
    os.mkdir(sourcedir)
    for file in files:
        shutil.copy2(file, os.path.join(sourcedir, file))
    for dir, options in dirs.items():
        shutil.copytree(dir, os.path.join(sourcedir, dir), ignore=shutil.ignore_patterns(*options["ignore"]))

def saveCommitId(release, builddir):
    if release["commitid"] is not None:
        with open(os.path.join(builddir, "release.json"), "r", encoding="utf8") as f:
            data = json.loads(f.read())
            data["commitid"] = release["commitid"]
        with open(os.path.join(builddir, "release.json"), "w", encoding="utf8") as f:
            f.write(json.dumps(data, sort_keys=True, ensure_ascii=False, indent=4))

def remove_readonly(func, path, _):
    os.chmod(path, stat.S_IWRITE)
    func(path)

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

#argparse
parser = argparse.ArgumentParser(description="build script for PS3GameUpdateDownloader")
parser.add_argument("-s", "--source", action="store_true", help="building a source version, mutually exclusive with '--compiled'")
parser.add_argument("-c", "--compiled", action="store_true", help="building a compiled version, mutually exclusive with '--source'")
parser.add_argument("-r", "--release", action="store_true", help="building a release version, mutually exclusive with '--debug'")
parser.add_argument("-d", "--debug",action="store_true", help="building a debug version, mutually exclusive with '--release'")
parser.add_argument("-z", "--zip", action="store_true", help="pack the build to a .zip file")
parser.add_argument("--docker", action="store_true", help='copy build zip to "./docker_output", requires --zip')
parser.add_argument("--githash", action="store", help="gives git commit hash to build script(mostly useful for docker builds)")
parser.add_argument("--winever", action="store", help="gives wine version to build script(mostly useful for docker builds)")

args = parser.parse_args()
#constants
builddir = "./dist/PS3GameUpdateDownloader"
buildlog = os.path.join(builddir, "build.log")
locdirname = "loc"
locdirbuildpath = os.path.join(builddir, locdirname)
imagedirname = "images"
iconpath = os.path.abspath(os.path.join(imagedirname, "icon.ico"))
NOW = datetime.datetime.now()
ARCHIVEFORMAT = "zip"
dockerdir = os.path.abspath("./docker_output")
mainpyifile = "main_ps3gud.py"
updaterpyifile = "updater.py"
winever = None
#get data from release.json
with open("release.json", "r", encoding="utf8") as f:
    release = json.loads(f.read())
release["commitid"] = None

#check parameters
action = ""
zip_check = False
docker = False
if args.compiled == True and args.source == True:
    print("You cant pass \"-c\" and \"-s\" to the buildscript.")
    sys.exit()
if args.debug == True and args.release == True:
    print("You cant pass \"-d\" and \"-r\" to the buildscript.")
    sys.exit()
if args.source == True and args.release == True:
    action = "sourcerelease"
if args.source == True and args.debug == True:
    action = "sourcedebug"
if args.compiled == True and args.release == True:
    action = "compilerelease"
if args.compiled == True and args.debug == True:
    action = "compiledebug"

if args.zip == True:
    zip_check = True
    zipname = "dist/PS3GameUpdateDownloader-"+release["version"]
    if args.docker == True:
        docker = True
        if os.path.exists(dockerdir) == False:
            os.makedirs(dockerdir)

if args.winever is not None:
    winever = args.winever
#auto config for build

suffix = ""
libc = ""
py = ""
if platform.system() == "Windows":
    suffix = ".exe"
    ostype = "win"
if platform.system() == "Linux":
    ostype = "linux"
    libc = f"{platform.libc_ver()[0]}{platform.libc_ver()[1]}-"
if platform.architecture()[0] == "32bit":
    bits = "32"
if platform.architecture()[0] == "64bit":
    bits = "64"
if args.compiled == True and args.zip == True:
    py = f"{platform.python_implementation()}{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}{sys.version_info.releaselevel}-"
arch = py + libc + ostype + bits

#get git commit id if git is found on path
if args.githash is not None:
    release["commitid"] = args.githash
elif (shutil.which("git") is not None) == True:
    call = shutil.which("git") + " rev-parse --short HEAD"
    call = call if platform.system() == "Windows" else shlex.split(call)
    release["commitid"] = subprocess.Popen(call, stdout=subprocess.PIPE).communicate()[0].decode("ascii").replace("\n", "")

print("build script for PS3GameUpdateDownloader")
if action == "":
    print("use '-h' for help")
else:
    print(f"build options:\nmode: {action}\narch: {arch}\ngit commit: {release['commitid']}\nzip: {zip_check}\ndocker: {docker}")

if action == "sourcerelease":
    #release running from source
    if os.path.exists(builddir):
        #delete old build
        shutil.rmtree(builddir, onexc=remove_readonly)
        os.makedirs(builddir)
    else:
        os.makedirs(builddir)
    with open(buildlog, "w") as f:
        #write header to buildlog
        buildheader(release, buildlog)
        #copy scripts
        print(f"copying scripts to '{builddir}'")
        shutil.copy2("main_ps3gud.py", os.path.join(builddir, "main_ps3gud.py"))
        shutil.copy2("utils.py", os.path.join(builddir, "utils.py"))
        shutil.copy2("updater.py", os.path.join(builddir, "updater.py"))
        shutil.copy2("PS3GUD.py", os.path.join(builddir, "PS3GUD.py"))
        shutil.copy2("gui.py", os.path.join(builddir, "gui.py"))
        #copy data
        print(f"copying data to '{builddir}'")
        copyData(builddir, locdirname, imagedirname, source=True)
        #save commitid
        saveCommitId(release, builddir)
        #validate & minify json files
        print("minifying & validating JSON files")
        minifyJSON(getJSONFiles())
        #build zip
        if zip_check == True:
            zipname += "-source"
            print(f"creating archive '{zipname}.{ARCHIVEFORMAT}'")
            shutil.make_archive(zipname, ARCHIVEFORMAT, "dist", os.path.relpath(builddir, "dist"))
            print(f"calculating checksum for archive '{zipname}.{ARCHIVEFORMAT}'")
            digest = createDigest(zipname+"."+ARCHIVEFORMAT)
            print(f"checksum written to '{zipname}.{ARCHIVEFORMAT}.sha256'\nchecksum: '{digest}'")
            if docker == True:
                print(f'copied build zip to "{dockerdir}"')
                shutil.copy2(zipname+"."+ARCHIVEFORMAT, os.path.join(dockerdir, os.path.basename(zipname)+"."+ARCHIVEFORMAT))
                shutil.copy2(zipname+"."+ARCHIVEFORMAT+".sha256", os.path.join(dockerdir, os.path.basename(zipname)+"."+ARCHIVEFORMAT+".sha256"))
   
if action == "sourcedebug":
    #debug running from source
    builddir += "Debug"
    buildlog = os.path.join(builddir, "build.log")
    if os.path.exists(builddir):
        #delete old build
        shutil.rmtree(builddir, onexc=remove_readonly)
        os.makedirs(builddir)
    else:
        os.makedirs(builddir)
    with open(buildlog, "w") as f:
        #write header to buildlog
        buildheader(release, buildlog)
        #copy scripts
        print(f"copying scripts to '{builddir}'")
        shutil.copy2("main_ps3gud.py", os.path.join(builddir, "main_ps3gud.py"))
        shutil.copy2("utils.py", os.path.join(builddir, "utils.py"))
        shutil.copy2("updater.py", os.path.join(builddir, "updater.py"))
        shutil.copy2("PS3GUD.py", os.path.join(builddir, "PS3GUD.py"))
        shutil.copy2("gui.py", os.path.join(builddir, "gui.py"))
        #copy data
        print(f"copying data to '{builddir}'")
        copyData(builddir, locdirname, imagedirname, source=True, debug=True)
        #save commitid
        saveCommitId(release, builddir)
        #validate json files
        print("validating JSON files")
        for file in getJSONFiles():
            validateJSON(file)
        #build zip
        if zip_check == True:
            zipname += "-source-debug"
            print(f"creating archive '{zipname}.{ARCHIVEFORMAT}'")
            shutil.make_archive(zipname, ARCHIVEFORMAT, "dist", os.path.relpath(builddir, "dist"))
            print(f"calculating checksum for archive '{zipname}.{ARCHIVEFORMAT}'")
            digest = createDigest(zipname+"."+ARCHIVEFORMAT)
            print(f"checksum written to '{zipname}.{ARCHIVEFORMAT}.sha256'\nchecksum: '{digest}'")
            if docker == True:
                print(f'copied build zip to "{dockerdir}"')
                shutil.copy2(zipname+"."+ARCHIVEFORMAT, os.path.join(dockerdir, os.path.basename(zipname)+"."+ARCHIVEFORMAT))
                shutil.copy2(zipname+"."+ARCHIVEFORMAT+".sha256", os.path.join(dockerdir, os.path.basename(zipname)+"."+ARCHIVEFORMAT+".sha256"))
        
if action == "compilerelease":
    #compiled release
    #delete old build
    if os.path.exists(builddir):
        shutil.rmtree(builddir, onexc=remove_readonly)
        os.makedirs(builddir)
    else:
        os.makedirs(builddir)
    #build main executable
    print("building main executable")
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
        "--icon="+iconpath,
        "--noupx"
    ]
    arg_main.append(mainpyifile)
    PyInstaller.__main__.run(arg_main)
    #build updater executable
    print("building updater executable")
    arg_updater = [
        "--name=PS3GUDup",
        "--clean",
        "--onefile",
        "--windowed",
        "--noupx"
    ]
    arg_updater.append(updaterpyifile)
    PyInstaller.__main__.run(arg_updater)
    #move executables to buildir
    print(f"copying executables to '{builddir}'")
    shutil.move("dist/ps3gud"+suffix, os.path.join(builddir, "ps3gud"+suffix))
    shutil.move("dist/PS3GUDup"+suffix, os.path.join(builddir, "PS3GUDup"+suffix))
    #copy data
    print(f"copying data to '{builddir}'")
    copyData(builddir, locdirname, imagedirname)
    #write header to buildlog
    buildheader(release, buildlog, pyiver=PyInstaller.__init__.__version__, winever=winever)
    #save commitid
    saveCommitId(release, builddir)
    #validate & minify json files
    print("minifying & validating JSON files")
    minifyJSON(getJSONFiles())
    #build zip
    if zip_check == True:
        zipname += "-"+arch
        print(f"creating archive '{zipname}.{ARCHIVEFORMAT}'")
        shutil.make_archive(zipname, ARCHIVEFORMAT, "dist", os.path.relpath(builddir, "dist"))
        print(f"calculating checksum for archive '{zipname}.{ARCHIVEFORMAT}'")
        digest = createDigest(zipname+"."+ARCHIVEFORMAT)
        print(f"checksum written to '{zipname}.{ARCHIVEFORMAT}.sha256'\nchecksum: '{digest}'")
        if docker == True:
                print(f'copied build zip to "{dockerdir}"')
                shutil.copy2(zipname+"."+ARCHIVEFORMAT, os.path.join(dockerdir, os.path.basename(zipname)+"."+ARCHIVEFORMAT))
                shutil.copy2(zipname+"."+ARCHIVEFORMAT+".sha256", os.path.join(dockerdir, os.path.basename(zipname)+"."+ARCHIVEFORMAT+".sha256"))

if action == "compiledebug":
    #compiled debug
    builddir += "Debug"
    buildlog = os.path.join(builddir, "build.log")
    #delete old build
    if os.path.exists(builddir):
        shutil.rmtree(builddir, onexc=remove_readonly)
        os.makedirs(builddir)
    else:
        os.makedirs(builddir)
    with open(buildlog, "w") as f:
        import PyInstaller.__main__
        import PyInstaller.__init__
        fh = logging.FileHandler(os.path.join(builddir, "build.log"))
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter('%(relativeCreated)d %(levelname)s: %(message)s'))
        log = logging.getLogger("PyInstaller")
        log.addHandler(fh)
        
        #build main executable
        print("building main executable")
        arg_main = [
            "--name=ps3gud",
            "--clean",
            "--onefile",
            "--icon="+iconpath,
            "--noupx",
            "--console"
        ]
        arg_main.append(mainpyifile)
        PyInstaller.__main__.run(arg_main)
        #build updater executable
        print("building updater executable")
        arg_updater = [
            "--name=PS3GUDup",
            "--clean",
            "--onefile",
            "--noupx",
            "--console"
        ]
        PyInstaller.__main__.run(arg_updater)
        #move executables to buildir
        print(f"copying executables to '{builddir}'")
        shutil.move("dist/ps3gud"+suffix, os.path.join(builddir, "ps3gud"+suffix))
        shutil.move("dist/PS3GUDup"+suffix, os.path.join(builddir, "PS3GUDup"+suffix))
        #copy data
        print(f"copying data to '{builddir}'")
        copyData(builddir, locdirname, imagedirname, debug=True)
        #write header to buildlog
        buildheader(release, buildlog, pyiver=PyInstaller.__init__.__version__, winever=winever)
        #save commitid
        saveCommitId(release, builddir)
        #validate json files
        print("validating JSON files")
        for file in getJSONFiles():
            validateJSON(file)
        #build zip
        if zip_check == True:
            zipname += "-"+arch+"-debug"
            print(f"creating archive '{zipname}.{ARCHIVEFORMAT}'")
            shutil.make_archive(zipname, ARCHIVEFORMAT, "dist", os.path.relpath(builddir, "dist"))
            print(f"calculating checksum for archive '{zipname}.{ARCHIVEFORMAT}'")
            digest = createDigest(zipname+"."+ARCHIVEFORMAT)
            print(f"checksum written to '{zipname}.{ARCHIVEFORMAT}.sha256'\nchecksum: '{digest}'")
            if docker == True:
                print(f'copied build zip to "{dockerdir}"')
                shutil.copy2(zipname+"."+ARCHIVEFORMAT, os.path.join(dockerdir, os.path.basename(zipname)+"."+ARCHIVEFORMAT))
                shutil.copy2(zipname+"."+ARCHIVEFORMAT+".sha256", os.path.join(dockerdir, os.path.basename(zipname)+"."+ARCHIVEFORMAT+".sha256"))
