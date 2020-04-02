#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#
# PS3GameUpdateDownloader by shinrax2

#builtin
import time
import tempfile
import os
import platform
import json
import subprocess
#local files
import utils

time.sleep(3) #wait 3 seconds to ensure main application has closed
if os.path.exists(os.path.join(tempfile.gettempdir(), "PS3GUDUpdate.json")) and os.path.isfile(os.path.join(tempfile.gettempdir(), "PS3GUDUpdate.json")):
    with open(os.path.join(tempfile.gettempdir(), "PS3GUDUpdate.json"), "r", encoding="utf8") as f:
        data = json.loads(f.read())

    rel = utils.UpdaterGithubRelease(os.path.join(data["dir"], "release.json"))
    resp = rel.checkForNewRelease()
    if type(resp) == dict:
        rel.downloadNewRelease(data["dir"])
        suffix = ""
        if platform.system() == "Windows":
            suffix = ".exe"
        subprocess.Popen(os.path.join(data["dir"], "ps3gud"+suffix))
