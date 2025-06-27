#!/usr/bin/bash

ZOTERO_DB='/Users/tgoodwin/Zotero/zotero.sqlite'
OBSIDIAN_VAULT='/Users/tgoodwin/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian-vault'


# # Get the directory where the script is located
# SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

python3 "$HOME/projects/zinc/main.py" --zotero-db="$ZOTERO_DB" --obsidian-vault="$OBSIDIAN_VAULT"
