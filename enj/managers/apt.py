"""apt - Debian / Ubuntu / derivatives."""

from __future__ import annotations

import shutil
import subprocess

from enj.managers.base import BaseManager


class AptManager(BaseManager):
    name = "apt"
    display_name = "apt (Debian/Ubuntu)"
    binary = "apt-get"
    native = True
    priority = 10
    sudo_ops = ("install", "remove", "update", "upgrade")

    @staticmethod
    def parse_search(stdout: str) -> list:
        names = []
        for line in stdout.splitlines():
            name = line.split(" - ", 1)[0].strip()
            if name:
                names.append(name)
        return names

    def search(self, query: str) -> list:
        if not shutil.which("apt-cache"):
            return []
        proc = subprocess.run(["apt-cache", "search", query], capture_output=True, text=True)
        if proc.returncode != 0:
            return []
        return self.parse_search(proc.stdout)

    def exists(self, package: str) -> bool:
        proc = subprocess.run(["apt-cache", "show", package], capture_output=True, text=True)
        return proc.returncode == 0 and "Package:" in proc.stdout

    def install(self, packages):
        return self._run(["install", "-y"] + packages, op="install")

    def remove(self, packages):
        return self._run(["remove", "-y"] + packages, op="remove")

    def update(self):
        return self._run(["update"], op="update")

    def upgrade(self):
        return self._run(["upgrade", "-y"], op="upgrade")

    def list_installed(self) -> list:
        if not shutil.which("dpkg"):
            return []
        proc = subprocess.run(["dpkg", "-l"], capture_output=True, text=True)
        pkgs = []
        for line in proc.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 2 and parts[0] == "ii":
                pkgs.append(parts[1])
        return pkgs

    def info(self, package: str) -> str:
        proc = self._sh(["apt-cache", "show", package])
        return proc.stdout or "(not found)"

    def server(self) -> str:
        import glob

        for path in ["/etc/apt/sources.list"] + glob.glob("/etc/apt/sources.list.d/*"):
            try:
                with open(path, encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith(("deb ", "deb-src ")):
                            parts = line.split()
                            if len(parts) > 1 and "://" in parts[1]:
                                return parts[1]
            except OSError:
                continue
        return "http://deb.debian.org/debian"
