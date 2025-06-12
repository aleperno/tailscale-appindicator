#!/usr/bin/env bash

WORKDIR="$(pwd)"
USERNAME="$(logname)"
TARGET_DIR="/opt/tailscale-appindicator"
RESOURCES_DIR="$TARGET_DIR/resources"
SCRIPTS_DIR="$TARGET_DIR/scripts"

if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

function delete_main_dir() {
  rm -rf $TARGET_DIR
}

function delete_desktop_files() {
  rm /usr/share/applications/tailscale_appindicator.desktop
  rm /etc/systemd/user/tailscale-appindicator.service
  sudo -u $USERNAME XDG_RUNTIME_DIR="/run/user/$(id -u $USERNAME)" systemctl --user daemon-reload
}

function remove_executable() {
  rm /usr/bin/tailscale-appindicator
}

function main() {
  delete_main_dir
  delete_desktop_files
  remove_executable
  update-desktop-database
}

main
