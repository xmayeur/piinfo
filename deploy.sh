#/bin/bash

sudo mkdir -p /user/share/piinfo/
sudo cp -f info.py /user/share/piinfo/info.py
sudo cp -f piinfo /etc/init.d
sudo chmod 0755 /etc/init.d/piinfo

sudo pip3 install -r requirements.txt

sudo pkill -9 -f info.py

sudo update-rc.d piinfo defaults
sudo systemctl enable piinfo

sudo service piinfo start