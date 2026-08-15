"""snap - Canonical's snap store."""

from __future__ import annotations

import subprocess

from enj.managers.base import BaseManager


class SnapManager(BaseManager):
    name = "snap"
    display_name = "snap"
    binary = "snap"
    native = False
    priority = 20

    SERVER = "https://api.snapcraft.io"
    sudo_ops = ("install", "remove", "update", "upgrade")

    @staticmethod
    def parse_search(stdout: str) -> list:
        names = []
        for line in stdout.splitlines():
            parts = line.split()
            if len(parts) >= 2 and not line.startswith(("Name", "Searching", "-")):
                if parts[0].strip() and parts[0].strip() not in names:
                    names.append(parts[0].strip())
        return names

    def search(self, query: str) -> list:
        proc = subprocess.run(["snap", "find", query], capture_output=True, text=True)
        if proc.returncode != 0:
            return []
        return self.parse_search(proc.stdout)

    def exists(self, package: str) -> bool:
        proc = subprocess.run(["snap", "find", "--name", package], capture_output=True, text=True)
        return proc.returncode == 0 and package in proc.stdout

    def install(self, packages):
        return self._run(["install"] + packages, op="install")

    def remove(self, packages):
        return self._run(["remove"] + packages, op="remove")

    def update(self):
        return 0  # snap updates on its own timer

    def upgrade(self):
        return self._run(["refresh"], op="upgrade")

    def list_installed(self) -> list:
        proc = self._run(["list"], op=None, stream=False)
        return [ln.split()[0] for ln in proc.stdout.splitlines() if ln.strip()][1:]

    def info(self, package: str) -> str:
        proc = subprocess.run(["snap", "info", package], capture_output=True, text=True)
        return proc.stdout or "(not found)"
