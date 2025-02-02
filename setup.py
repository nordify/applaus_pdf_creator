#!/usr/bin/env python3
import subprocess
from setuptools import setup

APP = ['pdf_creator.py']
DATA_FILES = ['icon.png']
OPTIONS = {
    'argv_emulation': True,
    'iconfile': 'icon.icns',
    'plist': {
        'CFBundleName': "PDF Creator",
        'CFBundleDisplayName': "PDF Creator",
        'CFBundleIdentifier': "one.nordify.applauspdfcreator",
        'CFBundleVersion': "1.0.0",
    },
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
