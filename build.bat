@echo off
pyinstaller -wF --noupx -n ps3gud main.py
mkdir dist\PS3GameUpdateDownloader
copy titledb.txt dist\PS3GameUpdateDownloader\titledb.txt
xcopy /E /I .\loc .\dist\PS3GameUpdateDownloader\loc
move dist\ps3gud.exe dist\PS3GameUpdateDownloader\ps3gud.exe