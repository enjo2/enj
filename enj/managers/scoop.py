"""scoop - a Windows package manager for CLI apps."""

from __future__ import annotations

import subprocess

from enj.managers.base import BaseManager


class ScoopManager(BaseManager):
    name = "scoop"
    display_name = "Scoop"
    binary = "scoop"
    native = False
    priority = 30

    SERVER = "https://github.com"
    sudo_ops = ()

    @staticmethod
    def parse_search(stdout: str) -> list:
        names = []
        for line in stdout.splitlines():
            if line.startswith("Results from") or "---" in line or "Nothing" in line:
                continue
            name = line.strip().split()[0] if line.strip() else ""
            if name and name not in names:
                names.append(name)
        return names

    def search(self, query: str) -> list:
        proc = subprocess.run(["scoop", "search", query], capture_output=True, text=True)
        if proc.returncode != 0:
            return []
        return self.parse_search(proc.stdout)

    def exists(self, package: str) -> bool:
        return bool(self.search(package))

    def install(self, packages):
        return self._run(["install"] + packages, op="install")

    def remove(self, packages):
        return self._run(["uninstall"] + packages, op="remove")

    def update(self):
        return 0

    def upgrade(self):
        return self._run(["update", "*"], op="upgrade")

    def list_installed(self) -> list:
        proc = self._run(["list"], op=None, stream=False)
        return [ln.split()[0] for ln in proc.stdout.splitlines() if ln.strip()]

    def info(self, package: str) -> str:
        proc = subprocess.run(["scoop", "info", package], capture_output=True, text=True)
        return proc.stdout or "(not found)"
