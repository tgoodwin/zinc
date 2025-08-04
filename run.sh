#!/usr/bin/bash

ZOTERO_DB='/Users/tgoodwin/Zotero/zotero.sqlite'
OBSIDIAN_VAULT='/Users/tgoodwin/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian-vault'
LOG_DIR="/Users/tgoodwin/projects/zinc/logs"
LOG_FILE="$LOG_DIR/zotero_sync_$(date +'%Y-%m-%d_%H-%M-%S').log"

# # Get the directory where the script is located
# SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

/Users/tgoodwin/.virtualenvs/zinc/bin/python3 "/Users/tgoodwin/projects/zinc/main.py" --zotero-db="$ZOTERO_DB" --obsidian-vault="$OBSIDIAN_VAULT"
