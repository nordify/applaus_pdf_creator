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
pyinstaller --windowed --name "PDF Creator" --icon=resources/icon.icns --add-data "resources/icon.png:." pdf_creator.py

codesign --force --deep --verbose --timestamp --entitlements resources/entitlements.plist --sign "$CERT_ID" "dist/PDF Creator.app"

find "dist/PDF Creator.app/Contents/Frameworks" -name "*.dylib" -exec codesign --force --timestamp --options runtime --entitlements resources/entitlements.plist --verbose -s "$CERT_ID" {} \;

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

# Codesign das DMG
codesign --force --deep --verbose --timestamp --entitlements resources/entitlements.plist --sign "$CERT_ID" "PDF Creator.dmg"
echo "Build done."

# if [ -z "$APP_SPECIFIC_PASSWORD" ]; then
#   echo "Error: APP_SPECIFIC_PASSWORD environment variable is not set."
#   exit 1
# fi

# echo "Submitting PDF Creator.dmg for notarization using notarytool..."
# xcrun notarytool submit "PDF Creator.dmg" \
#   --apple-id "nordify.dev@gmail.com" \
#   --team-id "JG7CFYYV5B" \
#   --password "$APP_SPECIFIC_PASSWORD" \
#   --wait

# RESULT=$?

# if [ $RESULT -ne 0 ]; then
#   echo "Notarization failed or was invalid."
#   exit 1
# fi

# echo "Notarization succeeded."

# echo "Stapling notarization ticket to PDF Creator.dmg..."
# xcrun stapler staple "PDF Creator.dmg"
# xcrun stapler validate "PDF Creator.dmg"

# echo "Build, signing, and notarization complete. PDF Creator.dmg is ready for distribution."