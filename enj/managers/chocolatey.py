"""chocolatey - a Windows package manager."""

from __future__ import annotations

import subprocess

from enj.managers.base import BaseManager


class ChocolateyManager(BaseManager):
    name = "choco"
    display_name = "Chocolatey"
    binary = "choco"
    native = False
    priority = 20

    SERVER = "https://community.chocolatey.org"
    sudo_ops = ()

    @staticmethod
    def parse_search(stdout: str) -> list:
        names = []
        for line in stdout.splitlines():
            parts = line.split()
            if len(parts) >= 2 and not line.startswith(("Chocolatey", "Searching")):
                name = parts[0].strip()
                if name and name not in names:
                    names.append(name)
        return names

    def search(self, query: str) -> list:
        proc = subprocess.run(["choco", "search", query], capture_output=True, text=True)
        if proc.returncode != 0:
            return []
        return self.parse_search(proc.stdout)

    def exists(self, package: str) -> bool:
        proc = subprocess.run(["choco", "search", package, "--exact"], capture_output=True, text=True)
        return proc.returncode == 0 and package in proc.stdout

    def install(self, packages):
        return self._run(["install", "-y"] + packages, op="install")

    def remove(self, packages):
        return self._run(["uninstall", "-y"] + packages, op="remove")

    def update(self):
        return 0

    def upgrade(self):
        return self._run(["upgrade", "-y", "all"], op="upgrade")

    def list_installed(self) -> list:
        proc = self._run(["list"], op=None, stream=False)
        return [ln.split()[0] for ln in proc.stdout.splitlines() if "Chocolatey" not in ln][1:]

    def info(self, package: str) -> str:
        proc = subprocess.run(["choco", "info", package], capture_output=True, text=True)
        return proc.stdout or "(not found)"
