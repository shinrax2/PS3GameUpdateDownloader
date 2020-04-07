pyinstaller -wF --noupx -n ps3gud main.py
pyinstaller -wF --noupx -n PS3GUDup updater.py
mkdir dist/PS3GameUpdateDownloader
cp -f titledb.txt dist/PS3GameUpdateDownloader/titledb.txt
cp -f release.json dist/PS3GameUpdateDownloader/release.json
cp -fr loc dist/PS3GameUpdateDownloader/
mv -f dist/ps3gud dist/PS3GameUpdateDownloader/ps3gud
mv -f dist/PS3GUDup dist/PS3GameUpdateDownloader/PS3GUDup