@echo off
pyinstaller -wF --noupx -n PS3GUD main.py
copy titledb.txt dist\titledb.txt