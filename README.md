# Zinc
Sync your local zotero database with your Obsidian Vault.

## Overview
Zinc creates a bridge between Zotero (reference management) and Obsidian (note-taking), allowing you to leverage the strengths of both tools. It reflects your Zotero library as markdown files that can be organized and manipulated in ways beyond what the Zotero UI affords.

## How it works
Zinc reads entries from your local Zotero SQLite database and creates a markdown file for each one. It adds Zotero metadata to each document's YAML frontmatter, making it easy to navigate and organize your research library using Obsidian's linking and tagging features.
While Zinc primarily syncs from Zotero to Obsidian, it treats Obsidian as the source of truth for specific content:

**Tags**
- Zotero tags are reflected in each markdown file's frontmatter
- Tags added within Obsidian are preserved during re-sync (using set union semantics)
- This allows you to maintain both Zotero's organizational system and add Obsidian-specific tags

**Notes**
- Each markdown file includes a dedicated `## Notes` section
- Content written in this section is preserved during future syncs

## Document structure
```
---
title: "Paper Title"
type: academic-paper
year: 2023
zotero-key: ABCDEF123
tags: 
  - cool-paper
  - software-testing
---

## Abstract
The original paper abstract from Zotero...

## Notes
Your personal notes about the paper that will be preserved across syncs.

## References
- Zotero Key: ABCDEF123
- DOI: 10.1234/example.doi
- [PDF](zotero://select/library/items/ABCDEF123)
```


## Usage
```
ZOTERO_DB='/Users/$USER/Zotero/zotero.sqlite'
OBSIDIAN_VAULT='/Users/$USER/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian-vault'

python3 main.py --zotero-db="$ZOTERO_DB" --obsidian-vault="$OBSIDIAN_VAULT"
```

## Scheduling
Add the following to your crontab (view with `crontab -e`) to run at the top of every hour
```
0 * * * * sh /Users/$USER/projects/zinc/run.sh
```


