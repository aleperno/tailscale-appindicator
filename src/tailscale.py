import subprocess
import os
import json
from typing import Callable, Optional
from enum import Enum

from constants import TAILSCALE_STATUS, TAILSCALE_CONNECT, TAILSCALE_DISCONNECT


class ConnectionStatus(Enum):
    UNKNOWN = 'Unknown'
    DISCONNECTED = 'Disconnected'
    CONNECTED = 'Connected'
    LOGGED_OUT = 'Logged Out'
    ERROR = 'Error'


TAILSCALE_RUNNING = ('Running', )
TAILSCALE_STOPPED = ('Stopped', )
TAILSCALE_UNKNOWN = ('Unknown', )

STATUS_MAPPING = {
    TAILSCALE_RUNNING: ConnectionStatus.CONNECTED,
    TAILSCALE_STOPPED: ConnectionStatus.DISCONNECTED,
    TAILSCALE_UNKNOWN: ConnectionStatus.UNKNOWN,
}


class TailscaleHandler:
    """
    Class to interface with tailscale commands
    """
    def __init__(self, sudo_enabled: bool = False):
        self.sudo_enabled = sudo_enabled

    def _get_scalate_method(self):
        return 'sudo' if self.sudo_enabled else 'pkexec'

    def _get_connect_cmd(self):
        return f"{self._get_scalate_method()} {TAILSCALE_CONNECT}".split()

    def _get_disconnect_cmd(self):
        return f"{self._get_scalate_method()} {TAILSCALE_DISCONNECT}".split()

    @staticmethod
    def check_status() -> ConnectionStatus:
        child = subprocess.run(TAILSCALE_STATUS.split(), capture_output=True, text=True)
        if child.returncode == 0:
            data = json.loads(child.stdout)
            status = data.get('BackendState', 'Unknown')
            for tailscale_status, connection_status in STATUS_MAPPING.items():
                if status in tailscale_status:
                    return connection_status
            return ConnectionStatus.UNKNOWN
        else:
            return ConnectionStatus.ERROR

    def connect(self) -> bool:
        child = subprocess.run(self._get_connect_cmd(),
                               capture_output=True,
                               text=True)
        print(f"El status fue {child.returncode}")
        return child.returncode == 0

    def disconnect(self) -> bool:
        child = subprocess.run(self._get_disconnect_cmd(),
                               capture_output=True,
                               text=True)
        print(f"El status fue {child.returncode}")
        return child.returncode == 0
