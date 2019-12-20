@echo off
pyinstaller -wF main.py
copy titledb.txt dist\titledb.txt
