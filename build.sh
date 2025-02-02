#!/bin/zsh
sudo rm -rf *.dmg
python setup.py py2app
rm -f .DS_Store
rm *.dmg
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