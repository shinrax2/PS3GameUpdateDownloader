@echo off
pyinstaller PS3GameUpdateDownloader.py
copy titledb.txt dist\PS3GameUpdateDownloader\titledb.txt
mkdir dist\PS3GameUpdateDownloader\downloadedPKGs
