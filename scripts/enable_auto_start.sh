#!/usr/bin/env bash

USERNAME="$(logname)"
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
RESOURCES_DIR="$(dirname $SCRIPT_DIR)/resources"

SERVICE_NAME="tailscale-appindicator.service"
SERVICE_FILE_PATH="$RESOURCES_DIR/$SERVICE_NAME"
TARGET_DIR="/etc/systemd/user/"

if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

echo "Copying tailscale-appindicator.service to the Systemd User directory"
cp $SERVICE_FILE_PATH $TARGET_DIR

echo "Refreshing the Daemon"
sudo -u $USERNAME XDG_RUNTIME_DIR="/run/user/$(id -u $USERNAME)" systemctl --user daemon-reload
sudo -u $USERNAME XDG_RUNTIME_DIR="/run/user/$(id -u $USERNAME)" systemctl --user enable $SERVICE_NAME
