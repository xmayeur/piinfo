#/bin/bash

mkdir -p /user/share/piinfo/
mv info.py /user/share/piinfo/info.py
mv piinfo /etc/init.d
sudo chmod 0755 /etc/init.d/piinfo

sudo pip3 install -r requirements.txt

pkill -9 -f info.py

sudo update-rc.d piinfo defaults
sudo systemctl enable piinfo

sudo service piinfo start