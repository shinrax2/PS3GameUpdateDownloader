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
import shlex

#local files
import utils

#pip packages
import PySimpleGUI as sg
    

time.sleep(1) #wait 1 seconds to ensure main application has closed
if os.path.exists(os.path.join(tempfile.gettempdir(), "PS3GUDUpdate.json")) and os.path.isfile(os.path.join(tempfile.gettempdir(), "PS3GUDUpdate.json")):
    with open(os.path.join(tempfile.gettempdir(), "PS3GUDUpdate.json"), "r", encoding="utf8") as f:
        data = json.loads(f.read())
    
    sg.change_look_and_feel("DarkAmber")
    layout = [
                [sg.Text("Checking for updates", size=(20, 2), key="updater_text")],
                [sg.ProgressBar(100, orientation="h", size=(20, 20), key="updater_progressbar")]
    ]
    window = sg.Window("PS3GUD Updater", layout)
    window.finalize()
    window.Refresh()
    text = window["updater_text"]
    bar = window["updater_progressbar"]
    rel = utils.UpdaterGithubRelease(os.path.join(data["dir"], "release.json"))
    resp = rel.checkForNewRelease()
    if isinstance(resp, dict):
        text.Update("Found new release!")
        rel.downloadNewRelease(data["dir"], window)
        suffix = utils.getExecutableSuffix()
        if utils.isAppFrozen():
            file = os.path.join(data["dir"], "ps3gud"+suffix)
        else:
            if platform.system() == "Windows":
                file = "py "+os.path.join(data["dir"], "main"+suffix)
            if platform.system() == "Linux":
                file = shlex.split("python3 "+os.path.join(data["dir"], "main"+suffix))
        subprocess.Popen(file)
    window.close()
