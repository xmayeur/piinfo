#!/bin/bash
sudo service piinfo stop
now=`date +%s`
# mkdir -p ./tmp$now
# cd ./tmp$now

# git clone https://github.com/xmayeur/piinfo .
sudo pip install -r requirements.txt
pyinstaller -F info.py
sudo mkdir -p /user/share/piinfo/
sudo cp -f ./dist/info /user/share/piinfo/info
sudo chmod 0755  /user/share/piinfo/info
# sudo cp -f piinfo.conf /etc
sudo cp -f piinfo /etc/init.d
sudo chmod 0755 /etc/init.d/piinfo

sudo pkill -9 -f info

sudo update-rc.d piinfo defaults
sudo systemctl enable piinfo

sudo service piinfo start
# cd ..
#  rm -fr ./tmp$now
