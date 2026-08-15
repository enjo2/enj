"""brew (Homebrew) - native on macOS, fallback on Linux."""

from __future__ import annotations

import subprocess

from enj.managers.base import BaseManager


class BrewManager(BaseManager):
    name = "brew"
    display_name = "Homebrew"
    binary = "brew"
    native = False
    priority = 30

    SERVER = "https://formulae.brew.sh"
    sudo_ops = ()

    @staticmethod
    def parse_search(stdout: str) -> list:
        names = []
        for line in stdout.splitlines():
            name = line.strip()
            if name and not name.startswith(("=", "Warning", "Formulae", "Casks")):
                if all(c.isalnum() or c in "-+@." for c in name):
                    names.append(name)
        return names

    def search(self, query: str) -> list:
        proc = subprocess.run(["brew", "search", query], capture_output=True, text=True)
        if proc.returncode not in (0, 1):
            return []
        return self.parse_search(proc.stdout)

    def exists(self, package: str) -> bool:
        proc = subprocess.run(["brew", "info", package], capture_output=True, text=True)
        return proc.returncode == 0

    def install(self, packages):
        return self._run(["install"] + packages, op="install")

    def remove(self, packages):
        return self._run(["uninstall"] + packages, op="remove")

    def update(self):
        return self._run(["update"], op="update")

    def upgrade(self):
        return self._run(["upgrade"], op="upgrade")

    def list_installed(self) -> list:
        proc = self._run(["list", "--formula"], op=None, stream=False)
        names = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
        proc2 = self._run(["list", "--cask"], op=None, stream=False)
        names += [ln.strip() for ln in proc2.stdout.splitlines() if ln.strip()]
        return names

    def info(self, package: str) -> str:
        proc = subprocess.run(["brew", "info", package], capture_output=True, text=True)
        return proc.stdout or "(not found)"
