import json
import getpass
import os
import subprocess
from pathlib import Path
from dataclasses import dataclass, asdict

CONFIG_DIR = Path.home() / ".config" / "tailscale_appindicator"

CONFIG_DIR.mkdir(parents=True, exist_ok=True)
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
SCRIPTS_PATH = os.path.join(DIR_PATH, 'scripts')

STATUS_FILE = CONFIG_DIR / "status.json"
SUDOERS_FILE = Path('/etc/sudoers.d/tailscale_appindicator')
SYSTEMD_TARGET_PATH = Path("/etc/systemd/user/")
SYSTEMD_SOURCE_PATH = os.path.join(DIR_PATH, '/resources/tailscale-appindicator.service')
ENABLE_AUTO_START_SCRIPT_PATH = os.path.join(SCRIPTS_PATH, 'enable_auto_start.sh')

DISABLE_AUTO_START_CMD = "systemctl --user disable tailscale-appindicator.service"

@dataclass
class AppIndicatorData:
    auto_retry: bool = False
    sudoers_configured: bool = False
    sudoers_enabled: bool = False
    auto_start: bool = False


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
    script_path = f'{DIR_PATH}/scripts/create_sudoers.sh'
    child = subprocess.run(['pkexec', '/usr/bin/bash', script_path],
                           capture_output=True,
                           text=True)
    return child.returncode == 0 if child else False


def disable_sudoers() -> bool:
    child = subprocess.run(['sudo', '/usr/bin/rm', '/etc/sudoers.d/tailscale_appindicator'],
                           capture_output=True,
                           text=True)
    return child.returncode == 0


def enable_autostart() -> bool:
    child = subprocess.run(['pkexec', '/usr/bin/bash', ENABLE_AUTO_START_SCRIPT_PATH])
    return child.returncode == 0


def disable_autostart() -> bool:
    child = subprocess.run(DISABLE_AUTO_START_CMD.split())
    return child.returncode == 0
