"""xbps - Void Linux."""

from __future__ import annotations

import subprocess

from enj.managers.base import BaseManager


class XbpsManager(BaseManager):
    name = "xbps"
    display_name = "xbps (Void)"
    binary = "xbps-install"
    native = True
    priority = 10

    SERVER = "https://repo-default.voidlinux.org/current"
    sudo_ops = ("install", "remove", "update", "upgrade")

    def search(self, query: str) -> list:
        proc = subprocess.run(["xbps-query", "-Rs", query], capture_output=True, text=True)
        if proc.returncode != 0:
            return []
        names = []
        for line in proc.stdout.splitlines():
            if " - " in line:
                name = line.split(" - ", 1)[0].strip()
                if name and name not in names:
                    names.append(name)
        return names

    def exists(self, package: str) -> bool:
        proc = subprocess.run(["xbps-query", "-R", package], capture_output=True, text=True)
        return proc.returncode == 0

    def install(self, packages):
        return self._run(["-y"] + packages, op="install")

    def remove(self, packages):
        proc = subprocess.run(["xbps-remove", "-y"] + packages, capture_output=True, text=True)
        return proc.returncode

    def update(self):
        return self._run(["-S"], op="update")

    def upgrade(self):
        return self._run(["-Syu"], op="upgrade")

    def list_installed(self) -> list:
        proc = subprocess.run(["xbps-query", "-l"], capture_output=True, text=True)
        return [ln.split()[1] for ln in proc.stdout.splitlines() if ln.strip()]

    def info(self, package: str) -> str:
        proc = subprocess.run(["xbps-query", "-R", package], capture_output=True, text=True)
        return proc.stdout or "(not found)"
