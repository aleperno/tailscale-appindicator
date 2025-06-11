import json
import getpass
import os
import subprocess
from pathlib import Path
from dataclasses import dataclass, asdict

CONFIG_DIR = Path.home() / ".config" / "tailscale_appindicator"

CONFIG_DIR.mkdir(parents=True, exist_ok=True)

STATUS_FILE = CONFIG_DIR / "status.json"
SUDOERS_FILE = Path('/etc/sudoers.d/tailscale_appindicator')
DIR_PATH = os.path.dirname(os.path.realpath(__file__))

@dataclass
class AppIndicatorData:
    auto_retry: bool = False
    sudoers_configured: bool = False
    sudoers_enabled: bool = False


def load_data() -> AppIndicatorData:
    try:
        with open(STATUS_FILE, 'r') as fd:
            data = json.load(fd)
            print(data)
            app_data = AppIndicatorData(**data)
            app_data.sudoers_configured = is_sudoers_configured()
            return app_data
    except:
        pass

    return AppIndicatorData()


def save_data(app_data: AppIndicatorData):
    with open(STATUS_FILE, 'w') as fd:
        json.dump(asdict(app_data), fd)


def is_sudoers_configured():
    return SUDOERS_FILE.exists()


def enable_sudoers() -> bool:
    child = subprocess.run(['pkexec', '/usr/bin/bash', f'{DIR_PATH}/create_sudoers.sh'],
                           capture_output=True,
                           text=True)
    if not child:
        return False
    return child.returncode == 0


def disable_sudoers() -> bool:
    child = subprocess.run(['sudo', '/usr/bin/rm', '/etc/sudoers.d/tailscale_appindicator'],
                           capture_output=True,
                           text=True)
    return child.returncode == 0
