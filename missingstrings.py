#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#
# missingstrings.py for PS3GameUpdateDownloader by shinrax2

#built-in
import json
import os

#constants
output = "missingstrings.txt"
locdir = "./loc/"
missing = {}

with open("./loc/en.json", "r", encoding="utf8") as f:
    master = json.loads(f.read())

locFiles = [pos_json for pos_json in os.listdir(locdir) if pos_json.endswith('.json')]

for file in locFiles:
    if file.endswith("en.json") == False:
        with open(os.path.join(locdir, file), "r", encoding="utf8") as f:
            loc = json.loads(f.read())
        short = loc["language_short"]["string"]
        miss = {}
        for k, v in master.items():
            try:
                loc[k]
            except KeyError:
                miss[k] = v
        missing[short] = miss

with open(output, "w", encoding="utf8") as f:
    f.write(json.dumps(missing, sort_keys=True, indent=4, ensure_ascii=False))