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

## Manual Usage
```
ZOTERO_DB='/path/to/your/Zotero/zotero.sqlite'
OBSIDIAN_VAULT='/path/to/your/ObsidianVault'

python3 main.py --zotero-db="$ZOTERO_DB" --obsidian-vault="$OBSIDIAN_VAULT"
```

## Automated Setup on macOS with `launchd`

For a robust, automated setup on macOS, it's recommended to bundle the script into a standalone application and schedule it with `launchd`. This method correctly handles permissions for accessing files in locations like iCloud Drive.

### 1. Install Dependencies
This project uses `py2app` to create the macOS application bundle. Install it using pip:
```bash
pip install py2app
```

### 2. Build the Application
Build the `Zinc.app` bundle by running the `setup.py` script:
```bash
python3 setup.py py2app
```
This will create a `dist` directory containing `Zinc.app`.

### 3. Configure the `launchd` Job
An example `launchd` plist file is provided as `com.user.zoterosync.plist.example`.

1.  **Copy the template:**
    ```bash
    cp com.user.zoterosync.plist.example com.user.zoterosync.plist
    ```
2.  **Edit `com.user.zoterosync.plist`:**
    Open the new file and replace the placeholder paths with the absolute paths for your system:
    *   `/path/to/your/project`: The full path to this project directory.
    *   `/path/to/your/Zotero/zotero.sqlite`: The full path to your Zotero database.
    *   `/path/to/your/ObsidianVault`: The full path to your Obsidian vault.

### 4. Grant Full Disk Access
For the application to access your Zotero database and Obsidian vault (especially if it's in iCloud), you must grant it Full Disk Access.

1.  Open **System Settings**.
2.  Go to **Privacy & Security** > **Full Disk Access**.
3.  Click the **+** button.
4.  Navigate to the `dist` folder inside your project directory.
5.  Select `Zinc.app` and click **Open**.

### 5. Schedule the Job
Move the configured `.plist` file to your `LaunchAgents` directory and load it using `launchctl`.

1.  **Move the plist file:**
    ```bash
    mv com.user.zoterosync.plist ~/Library/LaunchAgents/
    ```
2.  **Load the launch agent:**
    ```bash
    launchctl load ~/Library/LaunchAgents/com.user.zoterosync.plist
    ```

Zinc will now run automatically every hour. Logs will be created in the `logs` directory of this project.
