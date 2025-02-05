#!/bin/zsh
CERT_ID="Developer ID Application: Nordify UG (haftungsbeschrankt) (JG7CFYYV5B)"
sudo rm -rf *.dmg
sudo rm -f *.pdf
sudo rm -f *.zip
sudo rm -rf build/
sudo rm -rf dist/
sudo rm -rf .eggs/
rm -f .DS_Store

pip install pyinstaller
pyinstaller --windowed --name "PDF Creator" --icon=resources/icon.icns --add-data "resources:resources" pdf_creator.py

codesign --force --deep --verbose --timestamp --entitlements entitlements.plist --sign "$CERT_ID" "dist/PDF Creator.app"

find "dist/PDF Creator.app/Contents/Frameworks" -name "*.dylib" -exec codesign --force --timestamp --options runtime --entitlements entitlements.plist --verbose -s "$CERT_ID" {} \;

create-dmg \
  --volname "PDF Creator" \
  --window-size 600 450 \
  --background "resources/background.png" \
  --icon-size 100 \
  --icon "PDF Creator.app" 120 200 \
  --app-drop-link 480 200 \
  "PDF Creator.dmg" \
  "dist/PDF Creator.app"

echo "read 'icns' (-16455) \"resources/icon.icns\";" > icon.rsrc
Rez -append icon.rsrc -o "PDF Creator.dmg"
SetFile -a C "PDF Creator.dmg"
rm icon.rsrc

codesign --force --deep --verbose --timestamp --entitlements entitlements.plist --sign "$CERT_ID" "PDF Creator.dmg"
echo "Build done."