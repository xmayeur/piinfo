#!/bin/bash
sudo service piinfo stop
now=`date +%s`
mkdir -p ./tmp$now
cd ./tmp$now
git clone https://github.com/xmayeur/piinfo .
sudo mkdir -p /user/share/piinfo/
sudo cp -f info.py /user/share/piinfo/info.py
sudo cp -f piinfo.conf /etc
sudo cp -f piinfo /etc/init.d
sudo chmod 0755 /etc/init.d/piinfo

sudo pip3 install -r requirements.txt

sudo pkill -9 -f info.py

sudo update-rc.d piinfo defaults
sudo systemctl enable piinfo

sudo service piinfo start
cd ..
rm -fr ./tmp$now