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
sg.change_look_and_feel("DarkAmber")

layout1 = [
        [sg.Text("Enter TitleID")],
        [sg.Input(key="titleid"),sg.Button("Enter"),sg.Button("Config")],
        [sg.Output(size=(80,20), key="Out")],
        [sg.Exit()]
        ]

window = sg.Window("PS3 Game Update Downloader", layout1)
win2_act = False
ps3 = PS3GUD.PS3GUD(window)
ps3.loadConfig()
ps3.loadTitleDb()

while True:
    event, values = window.read()        
    if event in (None, 'Exit'):      
        break
    if event == "Config":
        window.hide()
        layoutConfig = [
                            [sg.Text("Download directory:"), sg.In(ps3.getConfig("dldir"), key="dldir"), sg.FolderBrowse(target="dldir")],
                            [sg.Text("Verify files:"), sg.Checkbox("", default=ps3.getConfig("verify"), key="verify")],
                            [sg.Text("Check if file was already downloaded:"),sg.Checkbox("", default=ps3.getConfig("checkIfAlreadyDownloaded"), key="checkIfAlreadyDownloaded")],
                            [sg.Text("Storage threshold (in %)"), sg.Spin([i for i in range(1, 100)], initial_value=ps3.getConfig("storageThreshold"), key="storageThreshold")],
                            [sg.Button("Cancel"),sg.Button("Save")]
                        ]
        winConfig = sg.Window("Configuration", layoutConfig)
        while True:
            evConfig, valConfig = winConfig.Read()
            if evConfig == "Cancel":
                winConfig.Close()
                window.UnHide()
                break
            elif evConfig == "Save":
                ps3.setConfig(valConfig["dldir"], valConfig["verify"], valConfig["checkIfAlreadyDownloaded"], valConfig["storageThreshold"])
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
            choices.append("all")
            data = updatePackToTable(ps3.getUpdates())
            lay2 = [
                    [sg.Text(ps3.getTitleNameFromId()+":")],
                    [sg.Table(values=data,headings=["Num","Version","Filesize","PS3 FW Version"])],
                    [sg.DropDown(choices, size=(3,8), key="drop"),sg.Button("OK"),sg.Exit()]
                   ]
            win2 = sg.Window("Select Updates", lay2)
            while True:
                ev2, val2 = win2.Read()
                if ev2 in (None, "Exit"):
                    win2.Close()
                    win2_act = False
                    window.UnHide()
                    tryDl = False
                    break
                elif ev2 == "OK" and val2["drop"] != "":
                    drop = val2["drop"]
                    if drop == "all":
                        drop = "all"
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