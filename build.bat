@echo off
pyinstaller -wF main.py
copy titledb.txt dist\titledb.txt
rename dist\main.exe dist\PS3GUD.exe
