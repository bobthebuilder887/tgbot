#!/usr/bin/bash
USER=$(whoami)
PYLOG=tgbot.log
SERVICE=tgbot.service
SCRIPT=tgbot

# Install the project using make
make install

# Check if a valid config.json file exists (runner requires a working config)
if [ ! -f config.json ]; then
	echo "config.json file not found"
	make clean
	exit 1
fi

# Perform first-time authentification for Telegram
./.venv/bin/python3 auth
# copy script to local bin
cp ./sys/$SCRIPT /usr/local/bin
# replace user_name with your user name in script file
sed -i -e "s/user_name/$USER/g" /usr/local/bin/$SCRIPT
# make the script executable
chmod +x /usr/local/bin/$SCRIPT
# Make a user directory if it does not exist
mkdir -p ~/.config/systemd/user
# Enable user's systemd instance to run after logout (as root):
sudo loginctl enable-linger $USER
# copy service file
cp ./sys/$SERVICE /etc/systemd/system/.config/systemd/user
# replace user_name with your user name in service file
sed -i -e "s/user_name/$USER/g" /home/$USER/.config/systemd/user/$SERVICE
# reload systemd
systemctl --user daemon-reload
# enable service
systemctl --user enable $SERVICE
# start service
systemctl --user start $SERVICE
# check python logs
less $PYLOG
