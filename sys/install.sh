#!/usr/bin/bash
USER=$(whoami)
PYLOG=tgbot.log
SERVICE=tgbot.service
SCRIPT=tgbot
PY=python3.12

# Update system
sudo apt-get update -y && sudo apt-get upgrade -y
# Make sure python is installed
sudo apt-get install -y $PY python3-pip
# Install the project using make using dev mode to be able to update the bot
make install_dev

# Check if a valid config.json file exists (runner requires a working config)
if [ ! -f config.json ]; then
	echo "config.json file not found, create a config file before you proceed"
	make clean
	exit 1
fi

# Perform first-time authentification for Telegram
./.venv/bin/auth-cli
# copy script to local bin
sudo cp ./sys/$SCRIPT /usr/local/bin
# replace user_name with your user name in script file
sudo sed -i -e "s/user_name/$USER/g" /usr/local/bin/$SCRIPT
# make the script executable for the user
sudo chmod +x /usr/local/bin/$SCRIPT
sudo chown $USER /usr/local/bin/$SCRIPT
# Make a user directory if it does not exist
mkdir -p ~/.config/systemd/user
# Enable user's systemd instance to run after logout (as root):
sudo loginctl enable-linger $USER
# copy service file
sudo cp ./sys/$SERVICE /home/$USER/.config/systemd/user
# replace user_name with your user name in service file
sudo sed -i -e "s/user_name/$USER/g" /home/$USER/.config/systemd/user/$SERVICE
# reload systemd
systemctl --user daemon-reload
# enable service
systemctl --user enable $SERVICE
# start service
systemctl --user start $SERVICE
# check python logs
less $PYLOG
