import subprocess
import os
import json
import re
import webbrowser
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
TAILSCALE_LOGGED_OFF = ('NeedsLogin', )

STATUS_MAPPING = {
    TAILSCALE_RUNNING: ConnectionStatus.CONNECTED,
    TAILSCALE_STOPPED: ConnectionStatus.DISCONNECTED,
    TAILSCALE_UNKNOWN: ConnectionStatus.UNKNOWN,
    TAILSCALE_LOGGED_OFF: ConnectionStatus.LOGGED_OUT,
}

LOGIN_URL_REGEX = ".*(?P<url>http(s?):\/\/login\.tailscale\.com[^\s]*).*"


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
        print("Me intento conectar")
        child = subprocess.Popen(self._get_connect_cmd(),
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 text=True)
        #child = subprocess.run(self._get_connect_cmd(),
        #                       capture_output=True,
        #                       text=True)

        for line in child.stdout:
            print(f"Proceso linea {line}")
            m = re.match(LOGIN_URL_REGEX, line)
            if m:
                print("Hubo Match")
                url = m.groupdict()['url']
                webbrowser.open(url)
            else:
                print("No hubo match")
        print("termino")
        #print(f"El status fue {child.returncode}")
        child.wait()
        return child.returncode == 0

    def disconnect(self) -> bool:
        child = subprocess.run(self._get_disconnect_cmd(),
                               capture_output=True,
                               text=True)
        print(f"El status fue {child.returncode}")
        return child.returncode == 0
