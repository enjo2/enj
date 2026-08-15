"""zypper - openSUSE."""

from __future__ import annotations

import subprocess

from enj.managers.base import BaseManager


class ZypperManager(BaseManager):
    name = "zypper"
    display_name = "zypper (openSUSE)"
    binary = "zypper"
    native = True
    priority = 30
    sudo_ops = ("install", "remove", "update", "upgrade")
    SERVER = "https://download.opensuse.org/repositories"

    @staticmethod
    def parse_search(stdout: str) -> list:
        names = []
        for line in stdout.splitlines():
            if "|" not in line:
                continue
            if line.strip().startswith("-") or set(line.replace("|", "").strip()) == {"-"}:
                continue
            cols = [c.strip() for c in line.split("|")]
            if len(cols) < 3:
                continue
            if cols[0] in ("S", "Status", "Type", "i+"):
                continue
            name = cols[1]
            if name and name not in names:
                names.append(name)
        return names

    def search(self, query: str) -> list:
        proc = subprocess.run(["zypper", "search", query], capture_output=True, text=True)
        if proc.returncode not in (0, 1, 104):
            return []
        return self.parse_search(proc.stdout)

    def exists(self, package: str) -> bool:
        proc = subprocess.run(["zypper", "info", package], capture_output=True, text=True)
        return proc.returncode == 0 and "Name:" in proc.stdout

    def install(self, packages):
        return self._run(["install", "-y", "--no-recommends"] + packages, op="install")

    def remove(self, packages):
        return self._run(["remove", "-y"] + packages, op="remove")

    def update(self):
        return self._run(["refresh"], op="update")

    def upgrade(self):
        return self._run(["update", "-y"], op="upgrade")

    def list_installed(self) -> list:
        proc = self._sh(["zypper", "packages", "--installed-only"])
        names = []
        for line in proc.stdout.splitlines():
            if "|" not in line:
                continue
            cols = [c.strip() for c in line.split("|")]
            if len(cols) >= 3 and cols[0].startswith("i"):
                name = cols[1]
                if name and name not in names:
                    names.append(name)
        return names

    def info(self, package: str) -> str:
        proc = self._sh(["zypper", "info", package])
        return proc.stdout or "(not found)"
