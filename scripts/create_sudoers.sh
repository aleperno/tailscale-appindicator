#!/usr/bin/env bash


USERNAME="$(logname)"
FILE_PATH="/etc/sudoers.d/tailscale_appindicator"

SUDO_TEMPLATE="$USERNAME ALL=(ALL:ALL) NOPASSWD:"
TAILSCALE="/usr/bin/tailscale"

TAIL_CONNECT="$SUDO_TEMPLATE $TAILSCALE up --accept-routes=true"
TAIL_DISCONNECT="$SUDO_TEMPLATE $TAILSCALE down"
REMOVE_SUDOERS="$SUDO_TEMPLATE /usr/bin/rm $FILE_PATH"

if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Remove existing sudo
if [ -e $FILE_PATH ]; then
  echo "EXISTE"
  rm $FILE_PATH
else
  echo "NO EXISTE"
fi

# Add sudo rules
echo $TAIL_CONNECT >> $FILE_PATH
echo $TAIL_DISCONNECT >> $FILE_PATH
echo $REMOVE_SUDOERS >> $FILE_PATH
