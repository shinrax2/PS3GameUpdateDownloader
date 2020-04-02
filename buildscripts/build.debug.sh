pyinstaller -F --noupx -n ps3gud main.py
pyinstaller -F --noupx -n PS3GUDup updater.py
mkdir dist/PS3GameUpdateDownloaderDebug
cp -f titledb.txt dist/PS3GameUpdateDownloaderDebug/titledb.txt
cp -f release.debug.json dist/PS3GameUpdateDownloaderDebug/release.json
cp -fr loc dist/PS3GameUpdateDownloaderDebug/
mv -f dist/ps3gud dist/PS3GameUpdateDownloaderDebug/ps3gud
mv -f dist/PS3GUDup dist/PS3GameUpdateDownloaderDebug/PS3GUDup