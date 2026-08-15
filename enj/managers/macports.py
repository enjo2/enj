"""macports - fallback package manager for macOS."""

from __future__ import annotations

import subprocess

from enj.managers.base import BaseManager


class MacportsManager(BaseManager):
    name = "macports"
    display_name = "MacPorts"
    binary = "port"
    native = False
    priority = 35

    SERVER = "https://distfiles.macports.org"
    sudo_ops = ("install", "remove", "update", "upgrade")

    @staticmethod
    def parse_search(stdout: str) -> list:
        names = []
        for line in stdout.splitlines():
            name = line.strip().split()[0] if line.strip() else ""
            if name and "@" not in name and name not in names:
                names.append(name)
        return names

    def search(self, query: str) -> list:
        proc = subprocess.run(["port", "search", query], capture_output=True, text=True)
        if proc.returncode != 0:
            return []
        return self.parse_search(proc.stdout)

    def exists(self, package: str) -> bool:
        proc = subprocess.run(["port", "info", package], capture_output=True, text=True)
        return proc.returncode == 0

    def install(self, packages):
        return self._run(["install"] + packages, op="install")

    def remove(self, packages):
        return self._run(["uninstall"] + packages, op="remove")

    def update(self):
        return self._run(["selfupdate"], op="update")

    def upgrade(self):
        return self._run(["upgrade", "outdated"], op="upgrade")

    def list_installed(self) -> list:
        proc = subprocess.run(["port", "installed"], capture_output=True, text=True)
        names = []
        for line in proc.stdout.splitlines():
            if "@" in line:
                name = line.strip().split("@")[0].strip()
                if name and name not in names:
                    names.append(name)
        return names

    def info(self, package: str) -> str:
        proc = subprocess.run(["port", "info", package], capture_output=True, text=True)
        return proc.stdout or "(not found)"
