#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#
# PS3GameUpdateDownloader by shinrax2

#pip packages
import PySimpleGUI as sg
#local files
import PS3GUD
import utils

def updatePackToTable(update):
    i = 1
    data = []
    for pack in update:
        row = [i, pack["version"], utils.formatSize(pack["size"]), pack["sysver"]]
        i+=1
        data.append(row)
    return data
ps3 = PS3GUD.PS3GUD()
ps3.loadConfig()
loc = utils.Loc()
loc.setLoc(ps3.getConfig("currentLoc"))
ps3.setLoc(loc)
sg.change_look_and_feel("DarkAmber")

layout1 = [
        [sg.Text(loc.getKey("window_main_titleid_label"))],
        [sg.Input(key="titleid"),sg.Button(loc.getKey("window_main_enter_btn"), key="Enter"),sg.Button(loc.getKey("window_main_config_btn") ,key="Config")],
        [sg.Output(size=(80,20), key="Out")],
        [sg.Button(loc.getKey("window_main_exit_btn"), key="Exit")]
        ]

window = sg.Window(loc.getKey("window_main_title"), layout1)
ps3.setWindow(window)
win2_act = False
ps3.logHeader()
ps3.loadTitleDb()

while True:
    event, values = window.read()        
    if event == "Exit":
        break
    if event in (None, "Exit"):
        break
    if event == "Config":
        window.hide()
        ll = loc.getLocs()
        locChoices = []
        for l in ll:
            locChoices.append(l["language_name"])
        
        layoutConfig = [
                            [sg.Text(loc.getKey("window_config_dldir_label")), sg.In(ps3.getConfig("dldir"), key="dldir"), sg.FolderBrowse(target="dldir")],
                            [sg.Text(loc.getKey("window_config_verify_label")), sg.Checkbox("", default=ps3.getConfig("verify"), key="verify")],
                            [sg.Text(loc.getKey("window_config_checkIfAlreadyDownloaded_label")),sg.Checkbox("", default=ps3.getConfig("checkIfAlreadyDownloaded"), key="checkIfAlreadyDownloaded")],
                            [sg.Text(loc.getKey("window_config_storageThreshold_label")), sg.Spin([i for i in range(1, 100)], initial_value=ps3.getConfig("storageThreshold"), key="storageThreshold")],
                            [sg.Text(loc.getKey("window_config_currentLoc_label")), sg.DropDown(locChoices, size=(8, 15), key="currentLoc")],
                            [sg.Button(loc.getKey("window_config_cancel_btn"), key="Cancel"),sg.Button(loc.getKey("window_config_save_btn"), key="Save")]
                        ]
        winConfig = sg.Window(loc.getKey("window_config_title"), layoutConfig)
        while True:
            evConfig, valConfig = winConfig.Read()
            if evConfig == "Cancel":
                winConfig.Close()
                window.UnHide()
                break
            elif evConfig in (None, "Exit"):
                winConfig.Close()
                window.UnHide()
                break
            elif evConfig == "Save" and valConfig["currentLoc"] != "":
                cL = valConfig["currentLoc"]
                for l in ll:
                    if cL == l["language_name"]:
                        cL = l["language_short"]
                config = { "dldir": valConfig["dldir"], "verify": valConfig["verify"], "checkIfAlreadyDownloaded": valConfig["checkIfAlreadyDownloaded"], "storageThreshold": valConfig["storageThreshold"], "currentLoc": cL }
                ps3.setConfig(config)
                loc.setLoc(cL)
                winConfig.Close()
                window.UnHide()
                break
    if event == "Enter":
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
            choices = []
            for x in range(1, updlen+1):
                choices.append(x)
            choices.append(loc.getKey("window_select_all_text"))
            data = updatePackToTable(ps3.getUpdates())
            lay2 = [
                    [sg.Text(ps3.getTitleNameFromId()+":")],
                    [sg.Table(values=data,headings=[loc.getKey("window_select_table_num"), loc.getKey("window_select_table_ver"), loc.getKey("window_select_table_size"), loc.getKey("window_select_table_sysver")])],
                    [sg.DropDown(choices, size=(3,8), key="drop"),sg.Button(loc.getKey("window_select_download_btn"), key="OK"),sg.Button(loc.getKey("window_select_cancel_btn"), key="Cancel")]
                   ]
            win2 = sg.Window(loc.getKey("window_select_title"), lay2)
            while True:
                ev2, val2 = win2.Read()
                if ev2 in (None, "Exit"):
                    win2.Close()
                    win2_act = False
                    window.UnHide()
                    tryDl = False
                    break
                elif ev2 == "Cancel":
                    win2.Close()
                    win2_act = False
                    window.UnHide()
                    tryDl = False
                    break
                elif ev2 == "OK" and val2["drop"] != "":
                    drop = val2["drop"]
                    if drop == loc.getKey("window_select_all_text"):
                        drop = loc.getKey("window_select_all_text")
                        for pack in ps3.getUpdates():
                            ps3.DlList.append(pack)
                        win2.Close()
                        win2_act = False
                        window.UnHide()
                        break
                    elif drop > 0 and drop < (len(ps3.getUpdates())+1):
                        drop = int(drop)-1
                        ps3.DlList.append(ps3.getUpdates()[drop])
                        win2.Close()
                        win2_act = False
                        window.UnHide()
                        break
        if tryDl == True:
            ps3.downloadFiles()
window.close()