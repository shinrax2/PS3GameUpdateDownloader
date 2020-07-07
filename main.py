#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#
# PS3GameUpdateDownloader by shinrax2

#builtin
import webbrowser
import tempfile
import platform
import os
import sys
import datetime
import traceback

#local files
import PS3GUD
import utils

#pip packages
import PySimpleGUI as sg

def updatePackToTable(update):
    data = []
    for pack in update:
        row = [pack["version"], utils.formatSize(pack["size"]), pack["sysver"]]
        data.append(row)
    return data
    
def queueToTable(queue, ps3):
    i = 1
    data = []
    if len(queue) > 0:
        for pack in queue:
            row = [i, ps3.getTitleNameFromId(pack["gameid"]), pack["gameid"], pack["version"], utils.formatSize(pack["size"])]
            i += 1
            data.append(row)
    else:
        data.append(["", "", "", "", ""])
    return data
    
def retranslateWindow(window, loc, items):
    for key, value in items.items():
        window[key].Update(loc.getKey(value))
        
def getCodeFromQueueData(queueData, resp):
    return queueData[resp][2]+"-"+queueData[resp][3]
    
def logUncaughtException(exctype, value, tb):
    now = str(datetime.datetime.now()).split(".")[0].replace(" ", "_").replace(":", "-")
    with open(os.path.join("logs", "Crash-"+now+".txt"), "w") as f:
        f.write("Uncaught exception:\nType: "+str(exctype)+"\nValue: "+str(value)+"\nTraceback:\n")
        for item in traceback.format_list(traceback.extract_tb(tb)):
            f.write(item)

#setup uncaught exception logging
sys.excepthook = logUncaughtException
    
#remove leftover files from updating
suffix = utils.getExecutableSuffix()
if os.path.exists(os.path.join(tempfile.gettempdir(), "PS3GUDup"+suffix)) and os.path.isfile(os.path.join(tempfile.gettempdir(), "PS3GUDup"+suffix)):
    os.remove(os.path.join(tempfile.gettempdir(), "PS3GUDup"+suffix)) 
if os.path.exists(os.path.join(tempfile.gettempdir(), "PS3GUDUpdate.json")) and os.path.isfile(os.path.join(tempfile.gettempdir(), "PS3GUDUpdate.json")):
    os.remove(os.path.join(tempfile.gettempdir(), "PS3GUDUpdate.json")) 
if utils.isAppFrozen() == False:
    if os.path.exists(os.path.join(tempfile.gettempdir(), "utils.py")) and os.path.isfile(os.path.join(tempfile.gettempdir(), "utils.py")):
        os.remove(os.path.join(tempfile.gettempdir(), "utils.py"))

#setup main classes
rel = utils.UpdaterGithubRelease("release.json")
ps3 = PS3GUD.PS3GUD()
loc = utils.Loc()
ps3.setLoc(loc)
ps3.loadConfig()
loc.setLoc(ps3.getConfig("currentLoc"))
sg.change_look_and_feel("DarkAmber")

layout1 = [ #layout for main window
        [sg.Text(loc.getKey("window_main_titleid_label"), key="window_main_titleid_label")],
        [sg.Input(key="titleid"),sg.Button(loc.getKey("window_main_enter_btn"), key="Enter", bind_return_key=True), sg.Button(loc.getKey("window_main_queue_btn"), key="Queue"), sg.Button(loc.getKey("window_main_config_btn") ,key="Config")],
        [sg.Text("", size=(30, 3), key="window_main_progress_label")],
        [sg.ProgressBar(100, orientation="h", size=(52.85, 20), key="window_main_progress_bar")],
        [sg.Output(size=(80,20), key="Out")],
        [sg.Button(loc.getKey("window_main_exit_btn"), key="Exit")]
]

window = sg.Window(loc.getKey("window_main_title")+" "+rel.getVersion(), layout1)
translateMainItems = {}
translateMainItems["window_main_titleid_label"] = "window_main_titleid_label"
translateMainItems["Enter"] = "window_main_enter_btn"
translateMainItems["Config"] = "window_main_config_btn"
translateMainItems["Queue"] = "window_main_queue_btn"
translateMainItems["Exit"] = "window_main_exit_btn"
ps3.setWindow(window)
win2_act = False
relCheck = False
tryDl = False
ps3.logHeader(rel.getVersion())
ps3.loadTitleDb()
if ps3.getConfig("checkForNewRelease"):
    relCheck = True
while True:
    if relCheck:
        data = rel.checkForNewRelease()
        if data == False:
            ps3.logger.log(loc.getKey("msg_relCheckError"))
            relCheck = False
        elif data == 1:
            ps3.logger.log(loc.getKey("msg_alreadyUpToDate"))
            relCheck = False
        elif data == 2:
            ps3.logger.log(loc.getKey("msg_NoReleaseArchiveForPlatformOrArch", [platform.system(), platform.architecture()[0], utils.isAppFrozen()]))
            relCheck = False
        else:
            ps3.logger.log(loc.getKey("msg_foundNewRelease", [data["version"]]))
            relCheck = False
            layoutRelNotify = [
                                [sg.Text(loc.getKey("window_relNotify_version_label", [rel.getVersion(), data["version"]]))],
                                [sg.Text(loc.getKey("window_relNotify_changelog_label"))],
                                [sg.Column([[sg.Text(rel.getChangelog())]]), sg.Slider(range=(1, len(rel.getChangelog().split("\n"))), default_value=1, orientation="v", size=(8, 10))],
                                [sg.Button(loc.getKey("window_relNotify_dl_btn"), key="dl"), sg.Button(loc.getKey("window_relNotify_web_btn"), key="web"), sg.Button(loc.getKey("window_relNotify_close_btn"), key="close")]
            ]
            winRelNotify = sg.Window(loc.getKey("window_relNotify_title"), layoutRelNotify)
            while True:
                evRel, valRel = winRelNotify.read()
                if evRel == "close":
                    winRelNotify.close()
                    break
                if evRel in (None, "Exit"):
                    winRelNotify.close()
                    break
                if evRel == "web":
                    webbrowser.open_new(data["releaseUrlWeb"])
                    winRelNotify.close()
                    break
                if evRel == "dl":
                    rel.startUpdater()
                    winRelNotify.close()
                    break
    event, values = window.read()
    if event == "Exit":
        break
    if event in (None, "Exit"):
        break
    if event == "Config" and tryDl == False:
        window.hide()
        ll = loc.getLocs()
        locChoices = []
        for l in ll:
            locChoices.append(l["language_name"])
        
        layoutConfig = [
                        [sg.Text(loc.getKey("window_config_dldir_label")), sg.In(ps3.getConfig("dldir"), key="dldir"), sg.FolderBrowse(target="dldir")],
                        [sg.Text(loc.getKey("window_config_verify_label")), sg.Checkbox("", default=ps3.getConfig("verify"), key="verify")],
                        [sg.Text(loc.getKey("window_config_checkIfAlreadyDownloaded_label")),sg.Checkbox("", default=ps3.getConfig("checkIfAlreadyDownloaded"), key="checkIfAlreadyDownloaded")],
                        [sg.Text(loc.getKey("window_config_checkForNewRelease_label")), sg.Checkbox("", default=ps3.getConfig("checkForNewRelease"), key="checkForNewRelease")],
                        [sg.Text(loc.getKey("window_config_storageThreshold_label")), sg.Spin([i for i in range(1, 100)], initial_value=ps3.getConfig("storageThreshold"), key="storageThreshold")],
                        [sg.Text(loc.getKey("window_config_currentLoc_label")), sg.OptionMenu(locChoices, size=(8, 15), key="currentLoc", default_value=loc.getKey("language_name"))],
                        [sg.Button(loc.getKey("window_config_cancel_btn"), key="Cancel"),sg.Button(loc.getKey("window_config_save_btn"), key="Save")]
        ]
        winConfig = sg.Window(loc.getKey("window_config_title"), layoutConfig)
        while True:
            evConfig, valConfig = winConfig.Read()
            if evConfig == "Cancel":
                winConfig.Close()
                window.UnHide()
                break
            if evConfig in (None, "Exit"):
                winConfig.Close()
                window.UnHide()
                break
            if evConfig == "Save" and valConfig["currentLoc"] != "":
                cL = valConfig["currentLoc"]
                for l in ll:
                    if cL == l["language_name"]:
                        cL = l["language_short"]
                config = { "dldir": valConfig["dldir"], "verify": valConfig["verify"], "checkIfAlreadyDownloaded": valConfig["checkIfAlreadyDownloaded"], "storageThreshold": valConfig["storageThreshold"], "currentLoc": cL }
                ps3.setConfig(config)
                loc.setLoc(cL)
                retranslateWindow(window, loc, translateMainItems)
                winConfig.Close()
                window.UnHide()
                break
    if event == "Enter"  and tryDl == False:
        tryDl = True
        ps3.checkForUpdates(values["titleid"])
        try:
            updlen = len(ps3.Updates[ps3.titleid])
        except KeyError:
            updlen = 0
            tryDl = False
        if updlen > 0 and win2_act == False:
            window.hide()
            win2_act = True
            data = updatePackToTable(ps3.getUpdates())
            lay2 = [
                    [sg.Text(loc.getKey("window_select_text_label", [ps3.getTitleNameFromId(), ps3.titleid]))],
                    [sg.Table(values=data, headings=[loc.getKey("window_select_table_ver"), loc.getKey("window_select_table_size"), loc.getKey("window_select_table_sysver")], key="Table", enable_events=True)],
                    [sg.Text(loc.getKey("window_select_help_label"), size=(45,2))],
                    [sg.Button(loc.getKey("window_select_download_btn"), key="OK", disabled=True),sg.Button(loc.getKey("window_select_queue_btn"), key="Queue", disabled=True), sg.Button(loc.getKey("window_select_cancel_btn"), key="Cancel")]
            ]
            win2 = sg.Window(loc.getKey("window_select_title"), lay2)
            while True:
                ev2, val2 = win2.Read()
                if len(val2["Table"]) > 0:
                    win2["OK"].Update(disabled=False)
                    win2["Queue"].Update(disabled=False)
                if len(val2["Table"]) == 0:
                    win2["OK"].Update(disabled=True)
                    win2["Queue"].Update(disabled=True)
                if ev2 in (None, "Exit"):
                    win2.Close()
                    win2_act = False
                    window.UnHide()
                    tryDl = False
                    break
                if ev2 == "Cancel":
                    win2.Close()
                    win2_act = False
                    window.UnHide()
                    tryDl = False
                    break
                if ev2 == "OK" and len(val2["Table"]) > 0:
                    if len(val2["Table"]) == 1:
                        ps3.DlList.addEntry(ps3.getUpdates()[val2["Table"][0]])
                        win2.Close()
                        win2_act = False
                        window.UnHide()
                        break
                    if len(val2["Table"]) > 1:
                        for row in val2["Table"]:
                            ps3.DlList.addEntry(ps3.getUpdates()[row])
                        win2.Close()
                        win2_act = False
                        window.UnHide()
                        break
                if ev2 == "Queue" and len(val2["Table"]) > 0:
                    if len(val2["Table"]) == 1:    
                        ps3.DlList.addEntry(ps3.getUpdates()[val2["Table"][0]])
                        win2.Close()
                        win2_act = False
                        window.UnHide()
                        tryDl = False
                        break
                    if len(val2["Table"]) > 1:
                        for row in val2["Table"]:
                            ps3.DlList.addEntry(ps3.getUpdates()[row])
                        win2.Close()
                        win2_act = False
                        window.UnHide()
                        tryDl = False
                        break
                        
    if event == "Queue" and tryDl == False:
        window.hide()
        queueData = queueToTable(ps3.DlList.queue, ps3)
        layQueue = [
                    [sg.Table(values=queueData, headings=[loc.getKey("window_queue_table_num"), loc.getKey("window_queue_table_game"), loc.getKey("window_queue_table_titleid"), loc.getKey("window_queue_table_ver"), loc.getKey("window_queue_table_size")], key="Table", enable_events=True)],
                    [sg.Text(loc.getKey("window_queue_totalsize_label", [utils.formatSize(ps3.DlList.getTotalDownloadSize())]), key="TotalSize", size=(20, 1))],
                    [sg.Button(loc.getKey("window_queue_moveup_btn"), key="Move Up", disabled=True), sg.Button(loc.getKey("window_queue_movedown_btn"), key="Move Down", disabled=True), sg.Button(loc.getKey("window_queue_remove_btn"), key="Remove", disabled=True)],
                    [sg.Button(loc.getKey("window_queue_download_btn"), key="Download"), sg.Button(loc.getKey("window_queue_close_btn"), key="Close")]
        ]
        windowQueue = sg.Window(loc.getKey("window_queue_title"), layQueue)
        while True:
            evQueue, valQueue = windowQueue.read()
            if len(valQueue["Table"]) == 0:
                windowQueue["Move Up"].Update(disabled=True)
                windowQueue["Move Down"].Update(disabled=True)
                windowQueue["Remove"].Update(disabled=True)
            if len(valQueue["Table"]) == 1:
                windowQueue["Move Up"].Update(disabled=False)
                windowQueue["Move Down"].Update(disabled=False)
                windowQueue["Remove"].Update(disabled=False)
            if len(valQueue["Table"]) > 1:
                windowQueue["Move Up"].Update(disabled=True)
                windowQueue["Move Down"].Update(disabled=True)
                windowQueue["Remove"].Update(disabled=False)
            if evQueue == "Move Up":
                if len(valQueue["Table"]) == 1:
                    if len(ps3.DlList.queue) > 1:
                        ps3.DlList.moveUp(getCodeFromQueueData(queueData, valQueue["Table"][0]))
                        queueData = queueToTable(ps3.DlList.queue, ps3)
                        windowQueue["Table"].Update(values=queueData)
            if evQueue == "Move Down":
                if len(valQueue["Table"]) == 1:
                    if len(ps3.DlList.queue) > 1:
                        ps3.DlList.moveDown(getCodeFromQueueData(queueData, valQueue["Table"][0]))
                        queueData = queueToTable(ps3.DlList.queue, ps3)
                        windowQueue["Table"].Update(values=queueData)
            if evQueue == "Remove":
                for row in valQueue["Table"]:
                    code = getCodeFromQueueData(queueData, row)
                    ps3.DlList.removeEntry(code)
                queueData = queueToTable(ps3.DlList.queue, ps3)
                windowQueue["Table"].Update(values=queueData)
                windowQueue["TotalSize"].Update(loc.getKey("window_queue_totalsize_label", [utils.formatSize(ps3.DlList.getTotalDownloadSize())]))
            if evQueue == "Download":
                tryDl = True
                windowQueue.Close()
                window.UnHide()
                break
            if evQueue in (None, "Exit"):
                windowQueue.Close()
                window.UnHide()
                break
            if evQueue == "Close":
                windowQueue.Close()
                window.UnHide()
                break
    if tryDl == True and len(ps3.DlList.queue) > 0:
        ps3.downloadFiles(window)
        window["window_main_progress_label"].Update("")
        window["window_main_progress_bar"].UpdateBar(0)
        tryDl = False
    if tryDl == True and len(ps3.DlList.queue) == 0:
        tryDl = False
window.close()