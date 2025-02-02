from setuptools import setup

APP = ['pdf_creator.py']
DATA_FILES = ['icon.png']  # Include any data files you need
OPTIONS = {
    'argv_emulation': False,  # Disable argv emulation to avoid Carbon issues
    'iconfile': 'icon.icns',  # Make sure you have an .icns file
    'plist': {
        'CFBundleName': 'PDF Creator',
        'CFBundleDisplayName': 'PDF Creator',
        'CFBundleIdentifier': 'com.yourdomain.pdfcreator',
        'CFBundleVersion': '1.0.0',
    },
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)