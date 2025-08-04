from setuptools import setup

APP = ['main.py']
APP_NAME = "Zinc"
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'plist': {
        'CFBundleName': APP_NAME,
        'CFBundleDisplayName': APP_NAME,
        'CFBundleGetInfoString': "Zotero to Obsidian Sync",
        'CFBundleIdentifier': "com.user.zoterosync",
        'CFBundleVersion': "0.1.0",
        'CFBundleShortVersionString': "0.1.0",
    }
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
