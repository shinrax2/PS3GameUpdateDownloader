@echo off
pyinstaller -F --noupx -n ps3gud main.py
pyinstaller -F --noupx -n PS3GUDup updater.py
mkdir dist\PS3GameUpdateDownloaderDebug
copy titledb.txt dist\PS3GameUpdateDownloaderDebug\titledb.txt
copy release.debug.json dist\PS3GameUpdateDownloaderDebug\release.json
xcopy /E /I /Y .\loc .\dist\PS3GameUpdateDownloaderDebug\loc
move dist\ps3gud.exe dist\PS3GameUpdateDownloaderDebug\ps3gud.exe
move dist\PS3GUDup.exe dist\PS3GameUpdateDownloaderDebug\PS3GUDup.exe