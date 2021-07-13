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

#local files
import PS3GUD
import utils

#pip packages
import PySimpleGUI as sg
import keyring

class Gui():
    def __init__(self):
        #setup uncaught exception logging
        sys.excepthook = utils.logUncaughtException
        
        #remove leftover files from updating
        utils.cleanupAfterUpdate()
        
        #setup main classes
        self.rel = utils.UpdaterGithubRelease("release.json")
        self.loc = utils.Loc()
        self.ps3 = PS3GUD.PS3GUD()
        self.ps3.setLoc(self.loc)
        self.ps3.loadConfig()
        self.loc.setLoc(self.ps3.getConfig("currentLoc"))
        self.ps3.loadTitleDb()
        
        #setup data
        self.TranslationItems = {}
        self.updateChecked = False
        self.proxydisabled = False
        self.noKeyrings = False
        self.keyring_support_shown = False
        if platform.system() == "Windows":
            self.iconpath = os.path.abspath(os.path.join("logos", "icon.ico"))
        else:
            self.iconpath = os.path.abspath(os.path.join("logos", "icon_16x16.png"))
        
        #check for avaiable keyring backends and disable proxy support if none is found
        rings = keyring.backend.get_all_keyring()
        if len(rings) == 1 and isinstance(rings[0], keyring.backends.fail.Keyring) == True:
            self.proxydisabled = True
            self.ps3.config["use_proxy"] = False
            self.noKeyrings = True
        
        #setup window style
        sg.change_look_and_feel("DarkAmber")
    
    def updatePackToTable(self, update):
        data = []
        for pack in update:
            row = [pack["version"], utils.formatSize(pack["size"]), pack["sysver"]]
            data.append(row)
        return data
        
    def queueToTable(self, queue, ps3):
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
        
    def retranslateWindow(self, window, loc, items):
        for key, value in items.items():
            window[key].Update(loc.getKey(value))
            
    def getCodeFromQueueData(self, queueData, resp):
        return queueData[resp][2]+"-"+queueData[resp][3]
    
    def mainWin(self):
        layout = [ #layout for main window
            [sg.Text(self.loc.getKey("window_main_titleid_label"), key="window_main_titleid_label", size=(50,1))],
            [sg.Input(key="titleid"),sg.Button(self.loc.getKey("window_main_enter_btn"), key="Enter", bind_return_key=True), sg.Button(self.loc.getKey("window_main_queue_btn"), key="Queue"), sg.Button(self.loc.getKey("window_main_config_btn") ,key="Config")],
            [sg.Text("", size=(30, 3), key="window_main_progress_label")],
            [sg.ProgressBar(100, orientation="h", size=(52.85, 20), key="window_main_progress_bar")],
            [sg.Output(size=(80,20), key="Out")],
            [sg.Button(self.loc.getKey("window_main_exit_btn"), key="Exit")]
        ]
        translateMainItems = {}
        translateMainItems["window_main_titleid_label"] = "window_main_titleid_label"
        translateMainItems["Enter"] = "window_main_enter_btn"
        translateMainItems["Config"] = "window_main_config_btn"
        translateMainItems["Queue"] = "window_main_queue_btn"
        translateMainItems["Exit"] = "window_main_exit_btn"
        self.TranslationItems["mainWindow"] = translateMainItems
        self.mainWindow = sg.Window(self.loc.getKey("window_main_title")+" "+self.rel.getVersion(), layout, finalize=True, icon=self.iconpath)
        self.tryDl = False
        self.ps3.setWindow(self.mainWindow)
        self.ps3.logHeader(self.rel.getVersion(), sg.version)
        self.ps3.logger.log(self.loc.getKey("msg_sonyPS3StoreShutdownNotice"))
        
        #main loop
        while True:
            if self.noKeyrings == True:
                if self.keyring_support_shown == False:
                    if self.ps3.getConfig("dont_show_again_keyring_support") == False:
                        self.keyring_supportWin()
            if self.ps3.useDefaultConfig == True:
                self.configWin(nocancel=True)
            if self.ps3.getConfig("checkForNewRelease"):
                if self.updateChecked == False:
                    self.newReleaseWin()
            event, value = self.mainWindow.read()
            if event == "Exit":
                break
            if event in (None, "Exit"):
                break
            if event == "Config" and self.tryDl == False:
                self.configWin()
            if event == "Queue" and self.tryDl == False:
                self.queueWin()
            if event == "Enter"  and self.tryDl == False:
                self.ps3.checkForUpdates(value["titleid"])
                self.selectWin()
            if self.tryDl == True and len(self.ps3.DlList.queue) > 0:
                self.ps3.downloadFiles(self.mainWindow)
                self.mainWindow["window_main_progress_label"].Update("")
                self.mainWindow["window_main_progress_bar"].UpdateBar(0)
                self.tryDl = False
            if self.tryDl == True and len(self.ps3.DlList.queue) == 0:
                self.tryDl = False

    def newReleaseWin(self):
        data = self.rel.checkForNewRelease()
        if data == False:
            self.ps3.logger.log(self.loc.getKey("msg_relCheckError"))
            self.updateChecked = True
        elif data == 1:
            self.ps3.logger.log(self.loc.getKey("msg_alreadyUpToDate"))
            self.updateChecked = True
        elif data == 2:
            self.ps3.logger.log(self.loc.getKey("msg_NoReleaseArchiveForPlatformOrArch", [platform.system(), platform.architecture()[0], utils.isAppFrozen()]))
            self.updateChecked = True
        else:
            self.ps3.logger.log(self.loc.getKey("msg_foundNewRelease", [data["version"]]))
            self.updateChecked = True
            layoutRelNotify = [
                [sg.Text(self.loc.getKey("window_relNotify_version_label", [self.rel.getVersion(), data["version"]]))],
                [sg.Text(self.loc.getKey("window_relNotify_changelog_label"))],
                [sg.Column([[sg.Text(self.rel.getChangelog(), size=(300, len(self.rel.getChangelog().split("\n"))*2))]], size=(700, 300), scrollable=True)],
                [sg.Button(self.loc.getKey("window_relNotify_dl_btn"), key="dl"), sg.Button(self.loc.getKey("window_relNotify_web_btn"), key="web"), sg.Button(self.loc.getKey("window_relNotify_close_btn"), key="close")]
            ]
            self.newReleaseWindow = sg.Window(self.loc.getKey("window_relNotify_title"), layoutRelNotify, icon=self.iconpath)
            while True:
                evRel, valRel = self.newReleaseWindow.read()
                if evRel == "close":
                    self.newReleaseWindow.close()
                    break
                if evRel in (None, "Exit"):
                    self.newReleaseWindow.close()
                    break
                if evRel == "web":
                    webbrowser.open_new(data["releaseUrlWeb"])
                    self.newReleaseWindow.close()
                    break
                if evRel == "dl":
                    self.rel.startUpdater()
                    self.newReleaseWindow.close()
                    break

    def configWin(self, nocancel=False):
        self.mainWindow.hide()
        ll = self.loc.getLocs()
        locChoices = []
        for l in ll:
            locChoices.append(l["language_name"])
        
        layoutConfig = [
            [sg.Text(self.loc.getKey("window_config_dldir_label"), size=(40,1)), sg.In(self.ps3.getConfig("dldir"), key="dldir"), sg.FolderBrowse(target="dldir")],
            [sg.Text(self.loc.getKey("window_config_verify_label"), size=(40,1)), sg.Checkbox("", default=self.ps3.getConfig("verify"), key="verify")],
            [sg.Text(self.loc.getKey("window_config_checkIfAlreadyDownloaded_label"), size=(40,1)),sg.Checkbox("", default=self.ps3.getConfig("checkIfAlreadyDownloaded"), key="checkIfAlreadyDownloaded")],
            [sg.Text(self.loc.getKey("window_config_checkForNewRelease_label"), size=(40,1)), sg.Checkbox("", default=self.ps3.getConfig("checkForNewRelease"), key="checkForNewRelease")],
            [sg.Text(self.loc.getKey("window_config_storageThreshold_label"), size=(40,1)), sg.Spin([i for i in range(1, 100)], initial_value=self.ps3.getConfig("storageThreshold"), key="storageThreshold")],
            [sg.Text(self.loc.getKey("window_config_currentLoc_label"), size=(40,1)), sg.OptionMenu(locChoices, size=(8, 15), key="currentLoc", default_value=self.loc.getKey("language_name"))],
            [sg.Text(self.loc.getKey("window_config_useproxy_label"), size=(40,1)), sg.Checkbox("", default=self.ps3.getConfig("use_proxy"), key="use_proxy", enable_events=True)],
            [sg.Text(self.loc.getKey("window_config_proxyip_label"), size=(40,1)), sg.In(self.ps3.getConfig("proxy_ip"), key="proxy_ip")],
            [sg.Text(self.loc.getKey("window_config_proxyport_label"), size=(40,1)), sg.In(self.ps3.getConfig("proxy_port"), key="proxy_port")],
            [sg.Text(self.loc.getKey("window_config_proxyuser_laber"), size=(40,1)), sg.In(self.ps3.getConfig("proxy_user"), key="proxy_user")],
            [sg.Text(self.loc.getKey("window_config_proxypass_label"), size=(40,1)), sg.In(self.ps3.getConfig("proxy_pass"), key="proxy_pass", password_char="*")],
            [sg.Button(self.loc.getKey("window_config_cancel_btn"), key="Cancel"), sg.Button(self.loc.getKey("window_config_save_btn"), key="Save", bind_return_key=True)]
        ]
        self.configWindow = sg.Window(self.loc.getKey("window_config_title"), layoutConfig, finalize=True, icon=self.iconpath)
        if nocancel == True:
            self.configWindow["Cancel"].Update(disabled=True)
        if self.proxydisabled == True:
            self.configWindow["use_proxy"].Update(disabled=True)
        if self.ps3.getConfig("use_proxy") == False:
            self.configWindow["proxy_ip"].Update(disabled=True)
            self.configWindow["proxy_port"].Update(disabled=True)
            self.configWindow["proxy_user"].Update(disabled=True)
            self.configWindow["proxy_pass"].Update(disabled=True)
        while True:
            evConfig, valConfig = self.configWindow.Read()
            if evConfig == "Cancel":
                self.configWindow.Close()
                self.mainWindow.UnHide()
                break
            if evConfig in (None, "Exit"):
                self.configWindow.Close()
                self.mainWindow.UnHide()
                break
            if evConfig == "use_proxy":
                if valConfig["use_proxy"] == True:
                    self.configWindow["proxy_ip"].Update(disabled=False)
                    self.configWindow["proxy_port"].Update(disabled=False)
                    self.configWindow["proxy_user"].Update(disabled=False)
                    self.configWindow["proxy_pass"].Update(disabled=False)
                else:
                    self.configWindow["proxy_ip"].Update(disabled=True)
                    self.configWindow["proxy_port"].Update(disabled=True)
                    self.configWindow["proxy_user"].Update(disabled=True)
                    self.configWindow["proxy_pass"].Update(disabled=True)
            if evConfig == "Save" and valConfig["currentLoc"] != "":
                cL = valConfig["currentLoc"]
                for l in ll:
                    if cL == l["language_name"]:
                        cL = l["language_short"]
                config = { "dldir": valConfig["dldir"], "verify": valConfig["verify"], "checkIfAlreadyDownloaded": valConfig["checkIfAlreadyDownloaded"], "storageThreshold": valConfig["storageThreshold"], "currentLoc": cL , "proxy_ip": valConfig["proxy_ip"], "proxy_port": valConfig["proxy_port"], "use_proxy": valConfig["use_proxy"]}
                self.ps3.setConfig(config)
                if self.ps3.getConfig("use_proxy") == True:
                    self.ps3.setProxyCredentials(valConfig["proxy_pass"], valConfig["proxy_user"])
                self.loc.setLoc(cL)
                self.ps3.setupProxy()
                self.retranslateWindow(self.mainWindow , self.loc, self.TranslationItems["mainWindow"])
                self.configWindow.Close()
                self.mainWindow.UnHide()
                break

    def selectWin(self):
        try:
            updlen = len(self.ps3.Updates[self.ps3.titleid])
        except KeyError:
            updlen = 0
            self.tryDl = False
        if updlen > 0:
            self.mainWindow.hide()
            data = self.updatePackToTable(self.ps3.getUpdates())
            lay2 = [
                [sg.Text(self.loc.getKey("window_select_text_label", [self.ps3.getTitleNameFromId(), self.ps3.titleid]))],
                [sg.Table(values=data, headings=[self.loc.getKey("window_select_table_ver"), self.loc.getKey("window_select_table_size"), self.loc.getKey("window_select_table_sysver")], key="Table", enable_events=True)],
                [sg.Text(self.loc.getKey("window_select_help_label"), size=(45,2))],
                [sg.Button(self.loc.getKey("window_select_download_btn"), key="OK", disabled=True),sg.Button(self.loc.getKey("window_select_queue_btn"), key="Queue", disabled=True), sg.Button(self.loc.getKey("window_select_cancel_btn"), key="Cancel")]
            ]
            self.selectWindow = sg.Window(self.loc.getKey("window_select_title"), lay2, icon=self.iconpath)
            while True:
                ev2, val2 = self.selectWindow.Read()
                if len(val2["Table"]) > 0:
                    self.selectWindow["OK"].Update(disabled=False)
                    self.selectWindow["Queue"].Update(disabled=False)
                if len(val2["Table"]) == 0:
                    self.selectWindow["OK"].Update(disabled=True)
                    self.selectWindow["Queue"].Update(disabled=True)
                if ev2 in (None, "Exit"):
                    self.selectWindow.Close()
                    self.mainWindow.UnHide()
                    self.tryDl = False
                    break
                if ev2 == "Cancel":
                    self.selectWindow.Close()
                    self.mainWindow.UnHide()
                    self.tryDl = False
                    break
                if ev2 == "OK" and len(val2["Table"]) > 0:
                    if len(val2["Table"]) == 1:
                        self.ps3.DlList.addEntry(self.ps3.getUpdates()[val2["Table"][0]])
                        self.selectWindow.Close()
                        self.mainWindow.UnHide()
                        self.tryDl = True
                        break
                    if len(val2["Table"]) > 1:
                        for row in val2["Table"]:
                            self.ps3.DlList.addEntry(self.ps3.getUpdates()[row])
                        self.selectWindow.Close()
                        self.mainWindow.UnHide()
                        self.tryDl = True
                        break
                if ev2 == "Queue" and len(val2["Table"]) > 0:
                    if len(val2["Table"]) == 1:    
                        self.ps3.DlList.addEntry(self.ps3.getUpdates()[val2["Table"][0]])
                        self.selectWindow.Close()
                        self.mainWindow.UnHide()
                        self.tryDl = False
                        break
                    if len(val2["Table"]) > 1:
                        for row in val2["Table"]:
                            self.ps3.DlList.addEntry(self.ps3.getUpdates()[row])
                        self.selectWindow.Close()
                        self.mainWindow.UnHide()
                        self.tryDl = False
                        break
                        

    def queueWin(self):
        self.mainWindow.hide()
        queueData = self.queueToTable(self.ps3.DlList.queue, self.ps3)
        layQueue = [
                    [sg.Table(values=queueData, headings=[self.loc.getKey("window_queue_table_num"), self.loc.getKey("window_queue_table_game"), self.loc.getKey("window_queue_table_titleid"), self.loc.getKey("window_queue_table_ver"), self.loc.getKey("window_queue_table_size")], key="Table", enable_events=True)],
                    [sg.Text(self.loc.getKey("window_queue_totalsize_label", [utils.formatSize(self.ps3.DlList.getTotalDownloadSize())]), key="TotalSize", size=(20, 1))],
                    [sg.Button(self.loc.getKey("window_queue_moveup_btn"), key="Move Up", disabled=True), sg.Button(self.loc.getKey("window_queue_movedown_btn"), key="Move Down", disabled=True), sg.Button(self.loc.getKey("window_queue_remove_btn"), key="Remove", disabled=True)],
                    [sg.Button(self.loc.getKey("window_queue_download_btn"), key="Download"), sg.Button(self.loc.getKey("window_queue_close_btn"), key="Close")]
        ]
        self.queueWindow = sg.Window(self.loc.getKey("window_queue_title"), layQueue, icon=self.iconpath)
        while True:
            evQueue, valQueue = self.queueWindow.read()
            if len(valQueue["Table"]) == 0:
                self.queueWindow["Move Up"].Update(disabled=True)
                self.queueWindow["Move Down"].Update(disabled=True)
                self.queueWindow["Remove"].Update(disabled=True)
            if len(valQueue["Table"]) == 1:
                self.queueWindow["Move Up"].Update(disabled=False)
                self.queueWindow["Move Down"].Update(disabled=False)
                self.queueWindow["Remove"].Update(disabled=False)
            if len(valQueue["Table"]) > 1:
                self.queueWindow["Move Up"].Update(disabled=True)
                self.queueWindow["Move Down"].Update(disabled=True)
                self.queueWindow["Remove"].Update(disabled=False)
            if evQueue == "Move Up":
                if len(valQueue["Table"]) == 1:
                    if len(self.ps3.DlList.queue) > 1:
                        self.ps3.DlList.moveUp(self.getCodeFromQueueData(queueData, valQueue["Table"][0]))
                        queueData = self.queueToTable(self.ps3.DlList.queue, self.ps3)
                        self.queueWindow["Table"].Update(values=queueData)
            if evQueue == "Move Down":
                if len(valQueue["Table"]) == 1:
                    if len(self.ps3.DlList.queue) > 1:
                        self.ps3.DlList.moveDown(self.getCodeFromQueueData(queueData, valQueue["Table"][0]))
                        queueData = self.queueToTable(ps3.DlList.queue, ps3)
                        self.queueWindow["Table"].Update(values=queueData)
            if evQueue == "Remove":
                for row in valQueue["Table"]:
                    code = self.getCodeFromQueueData(queueData, row)
                    self.ps3.DlList.removeEntry(code)
                queueData = self.queueToTable(self.ps3.DlList.queue, self.ps3)
                self.queueWindow["Table"].Update(values=queueData)
                self.queueWindow["TotalSize"].Update(self.loc.getKey("window_queue_totalsize_label", [utils.formatSize(self.ps3.DlList.getTotalDownloadSize())]))
            if evQueue == "Download":
                self.tryDl = True
                self.queueWindow.Close()
                self.mainWindow.UnHide()
                break
            if evQueue in (None, "Exit"):
                self.queueWindow.Close()
                self.mainWindow.UnHide()
                break
            if evQueue == "Close":
                self.queueWindow.Close()
                self.mainWindow.UnHide()
                break

    def keyring_supportWin(self):
        self.keyring_support_shown = True
        keyring_url = "https://github.com/jaraco/keyring"
        layout = [
            [sg.Text(self.loc.getKey("window_keyring_support_info_label", [keyring_url]))],
            [sg.Checkbox(self.loc.getKey("window_keyring_support_dont_show_again_label"), default=False, key="dont_show_again"), sg.Button(self.loc.getKey("window_keyring_support_ok_btn"), key="ok"), sg.Button(self.loc.getKey("window_keyring_support_browser_btn"), key="browser")]
        ]
        self.mainWindow.hide()
        self.keyring_supportWindow = sg.Window(self.loc.getKey("window_keyring_support_title"), layout, size=(600,100), icon=self.iconpath)
        while True:
            ev, val = self.keyring_supportWindow.read()
            if ev == "ok":
                if val["dont_show_again"] == True:
                    self.ps3.config["dont_show_again_keyring_support"] = True
                    self.ps3.saveConfig()
                self.keyring_supportWindow.Close()
                self.mainWindow.UnHide()
                break
            if ev == "browser":
                webbrowser.open_new(keyring_url)
            if ev in (None, "Exit"):
                self.keyring_supportWindow.Close()
                self.mainWindow.UnHide()
                break