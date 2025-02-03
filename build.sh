#!/bin/zsh
CERT_ID="Developer ID Application: Nordify UG (haftungsbeschrankt) (JG7CFYYV5B)"
sudo rm -rf *.dmg
rm -f .DS_Store
python setup.py py2app
codesign --force --deep --verbose --timestamp --entitlements entitlements.plist --sign "$CERT_ID" "dist/PDF Creator.app"
find "dist/PDF Creator.app/Contents/Resources/lib/python3.9/PyQt5/Qt5" -name "*.dylib" -exec codesign --force --timestamp --options runtime --entitlements entitlements.plist --verbose -s "$CERT_ID" {} \;

create-dmg \
  --volname "PDF Creator" \
  --window-size 600 450 \
  --background "background.png" \
  --icon-size 100 \
  --icon "PDF Creator.app" 120 200 \
  --app-drop-link 480 200 \
  "PDF Creator.dmg" \
  "dist/PDF Creator.app"

echo "read 'icns' (-16455) \"icon.icns\";" > icon.rsrc
Rez -append icon.rsrc -o "PDF Creator.dmg"
SetFile -a C "PDF Creator.dmg"
rm icon.rsrc

codesign --force --deep --verbose --timestamp --entitlements entitlements.plist --sign "$CERT_ID" "PDF Creator.dmg"
zip "PDFCreator.zip" "PDF Creator.dmg"
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