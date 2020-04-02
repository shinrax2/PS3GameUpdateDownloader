@echo off
pyinstaller -wF --noupx -n ps3gud main.py
pyinstaller -F --noupx -n PS3GUDup updater.py
mkdir dist\PS3GameUpdateDownloader
copy titledb.txt dist\PS3GameUpdateDownloader\titledb.txt
copy release.json dist\PS3GameUpdateDownloader\release.json
xcopy /E /I /Y .\loc .\dist\PS3GameUpdateDownloader\loc
move dist\ps3gud.exe dist\PS3GameUpdateDownloader\ps3gud.exe
move dist\PS3GUDup.exe dist\PS3GameUpdateDownloader\PS3GUDup.exe