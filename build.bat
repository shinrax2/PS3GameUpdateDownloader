@echo off
SET upx-dir=""
pyinstaller --upx-dir %upx-dir% PS3GUD.py
copy titledb.txt dist\PS3GUD\titledb.txt
mkdir dist\PS3GUD\downloadedPKGs
