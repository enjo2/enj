"""AUR - Arch User Repository, via a helper like paru or yay."""

from __future__ import annotations

import shutil
import subprocess

from enj.managers.base import BaseManager


class AurManager(BaseManager):
    name = "aur"
    display_name = "AUR"
    binary = None  # resolved to paru or yay
    native = False
    priority = 15
    sudo_ops = ()  # paru/yay handle sudo themselves
    SERVER = "https://aur.archlinux.org"

    def available(self) -> bool:
        self.binary = None
        for candidate in ("paru", "yay"):
            if shutil.which(candidate):
                self.binary = candidate
                break
        return self.binary is not None

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
        proc = subprocess.run([self.binary, "-Ss", query], capture_output=True, text=True)
        if proc.returncode not in (0, 1):
            return []
        return self.parse_search(proc.stdout)

    def exists(self, package: str) -> bool:
        proc = subprocess.run([self.binary, "-Si", package], capture_output=True, text=True)
        return proc.returncode == 0

    def install(self, packages):
        return self._run(["-S", "--noconfirm", "--needed"] + packages, op="install")

    def remove(self, packages):
        if shutil.which("pacman"):
            return subprocess.call(
                ["sudo", "pacman", "-Rns", "--noconfirm"] + packages
                if not _root()
                else ["pacman", "-Rns", "--noconfirm"] + packages
            )
        return 0

    def update(self):
        return self._run(["-Sy"], op="update")

    def upgrade(self):
        return self._run(["-Syu", "--noconfirm"], op="upgrade")

    def list_installed(self) -> list:
        if shutil.which("pacman"):
            proc = subprocess.run(["pacman", "-Q"], capture_output=True, text=True)
            return [ln.split()[0] for ln in proc.stdout.splitlines() if ln.strip()]
        return []

    def info(self, package: str) -> str:
        proc = subprocess.run([self.binary, "-Si", package], capture_output=True, text=True)
        return proc.stdout or "(not found)"


def _root():
    from enj.osdetect import is_root

    return is_root()
