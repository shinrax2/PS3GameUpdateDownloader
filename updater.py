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
import sys

#local files
import utils

#pip packages
import PySimpleGUI as sg
    
if os.path.exists(os.path.join(tempfile.gettempdir(), "PS3GUDUpdate.json")) and os.path.isfile(os.path.join(tempfile.gettempdir(), "PS3GUDUpdate.json")):
    with open(os.path.join(tempfile.gettempdir(), "PS3GUDUpdate.json"), "r", encoding="utf8") as f:
        data = json.loads(f.read())
    sg.change_look_and_feel("DarkAmber")
    layout = [
                [sg.Text("Waiting for main application to exit", size=(40, 3), key="updater_text")],
                [sg.ProgressBar(100, orientation="h", size=(40, 20), key="updater_progressbar")]
    ]
    window = sg.Window("PS3GUD Updater", layout)
    window.finalize()
    window.Refresh()
    text = window["updater_text"]
    bar = window["updater_progressbar"]
    utils.waitForMainAppExit(pid = data["pid"], window = window)
    text.Update("Checking for updates")
    window.Refresh()
    rel = utils.UpdaterGithubRelease(os.path.join(data["dir"], "release.json"))
    resp = rel.checkForNewRelease()
    if isinstance(resp, dict):
        text.Update("Found new release!")
        rel.downloadNewRelease(data["dir"], window)
        exename = utils.getMainExecutableBasename()+utils.getExecutableSuffix()
        if utils.isAppFrozen():
            file = os.path.join(data["dir"], exename)
        else:
            file = "python3 "+os.path.join(data["dir"], exename)
            if platform.system() == "Linux":
                file = shlex.split(file)
        subprocess.Popen(file)
    window.close()
