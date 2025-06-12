#!/usr/bin/env bash

WORKDIR="$(pwd)"
TARGET_DIR="/opt/tailscale-appindicator"
RESOURCES_DIR="$TARGET_DIR/resources"
SCRIPTS_DIR="$TARGET_DIR/scripts"

if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

function copy_resource_files() {
  # Copy python files and other required resources
  mkdir -p $RESOURCES_DIR
  cp -r "$WORKDIR"/*.py $TARGET_DIR
  cp -r "$WORKDIR"/resources/*.svg $RESOURCES_DIR
  cp -r "$WORKDIR/scripts/create_sudoers.sh" $SCRIPTS_DIR
}

function copy_desktop_files() {
  cp "$WORKDIR/resources/tailscale_appindicator.desktop" /usr/share/applications/
  #cp "$WORKDIR/resources/tailscale_appindicator.desktop" /etc/xdg/autostart/
  cp "$WORKDIR/resources/tailscale-appindicator.service" /etc/systemd/user
  systemctl --user daemon-reload
}

function executable() {
  ln -s "$TARGET_DIR/main.py" "/usr/bin/tailscale-appindicator" 2> /dev/null
  chmod +x "$TARGET_DIR/main.py"
}

function install_icon() {
  cp "$RESOURCES_DIR/tailscale_main.svg" /usr/share/icons/hicolor/scalable/apps/tailscale-appindicator.svg
  gtk-update-icon-cache -f /usr/share/icons/hicolor
  update-desktop-database
}


function main() {
  copy_resource_files
  copy_desktop_files
  executable
  install_icon
}

main
