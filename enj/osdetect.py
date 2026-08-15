"""OS / distro detection: figure out which native package manager to prefer."""

from __future__ import annotations

import platform
from typing import Optional

NATIVE_BY_DISTRO = {
    "arch": "pacman",
    "manjaro": "pacman",
    "endeavouros": "pacman",
    "debian": "apt",
    "ubuntu": "apt",
    "linuxmint": "apt",
    "kali": "apt",
    "pop": "apt",
    "zorin": "apt",
    "fedora": "dnf",
    "rhel": "dnf",
    "centos": "dnf",
    "alma": "dnf",
    "rocky": "dnf",
    "opensuse": "zypper",
    "suse": "zypper",
    "alpine": "apk",
    "gentoo": "emerge",
    "void": "xbps",
    "nixos": "nix",
    "amazon": "dnf",
}


def system() -> str:
    return platform.system()


def read_os_release() -> dict:
    data = {}
    try:
        with open("/etc/os-release", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if "=" in line:
                    k, _, v = line.partition("=")
                    data[k.strip()] = v.strip().strip('"').strip("'")
    except OSError:
        pass
    return data


def _tokens() -> set:
    data = read_os_release()
    ids = {data.get("ID", "").lower(), data.get("ID_LIKE", "").lower()}
    tokens = set()
    for ident in ids:
        for word in ident.split():
            tokens.add(word)
    return tokens


def native_manager_name() -> Optional[str]:
    """Return the name of the OS's native package manager, or None."""
    sysname = system()
    if sysname == "Darwin":
        return "brew"
    if sysname == "Windows":
        return None
    tokens = _tokens()
    for distro, manager in NATIVE_BY_DISTRO.items():
        if distro in tokens:
            return manager
    return None


def is_root() -> bool:
    if system() == "Windows":
        import ctypes

        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            return False
    import os

    try:
        return os.geteuid() == 0
    except AttributeError:
        return False
