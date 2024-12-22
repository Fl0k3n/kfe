import os
import platform
import sys
from typing import Optional


def is_linux() -> bool:
    return sys.platform == 'linux'

def is_mac_os() -> bool:
    return sys.platform == 'darwin'

def is_windows() -> bool:
    return sys.platform == 'win32'

def is_apple_silicon() -> bool:
    return is_mac_os() and platform.machine() == 'arm64'

def get_home_dir_path() -> Optional[str]:
    return os.getenv('USERPROFILE') if is_windows() else os.getenv('HOME')
