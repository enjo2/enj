"""pacman - Arch Linux / Manjaro and derivatives."""

from __future__ import annotations

import subprocess

from enj.managers.base import BaseManager


class PacmanManager(BaseManager):
    name = "pacman"
    display_name = "pacman (Arch)"
    binary = "pacman"
    native = True
    priority = 10
    sudo_ops = ("install", "remove", "update", "upgrade")

    @staticmethod
    def parse_search(stdout: str) -> list:
        names = []
        for line in stdout.splitlines():
            if line and line[0].isalpha() and "/" in line:
                name = line.split()[0].rsplit("/", 1)[-1]
                if name not in names:
                    names.append(name)
        return names

    def search(self, query: str) -> list:
        proc = subprocess.run(["pacman", "-Ss", query], capture_output=True, text=True)
        if proc.returncode not in (0, 1):
            return []
        return self.parse_search(proc.stdout)

    def exists(self, package: str) -> bool:
        proc = subprocess.run(["pacman", "-Si", package], capture_output=True, text=True)
        return proc.returncode == 0

    def install(self, packages):
        return self._run(["-S", "--noconfirm", "--needed"] + packages, op="install")

    def remove(self, packages):
        return self._run(["-Rns", "--noconfirm"] + packages, op="remove")

    def update(self):
        return self._run(["-Sy"], op="update")

    def upgrade(self):
        return self._run(["-Syu", "--noconfirm"], op="upgrade")

    def list_installed(self) -> list:
        proc = self._run(["-Q"], op=None, stream=False)
        return [ln.split()[0] for ln in proc.stdout.splitlines() if ln.strip()]

    def info(self, package: str) -> str:
        proc = self._run(["-Si", package], op=None, stream=False, check=False)
        return proc.stdout or proc.stderr or "(not found)"

    def server(self) -> str:
        try:
            with open("/etc/pacman.d/mirrorlist", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("Server = "):
                        return line.split("=", 1)[1].strip().rstrip("/")
        except OSError:
            pass
        return "https://geo.mirror.pkgbuild.com"
