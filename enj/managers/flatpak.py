"""flatpak - cross-distro desktop app store."""

from __future__ import annotations

import subprocess

from enj.managers.base import BaseManager


class FlatpakManager(BaseManager):
    name = "flatpak"
    display_name = "flatpak"
    binary = "flatpak"
    native = False
    priority = 10

    SERVER = "https://dl.flathub.org"
    sudo_ops = ()  # flatpak handles per-user remotes; system installs are per-user friendly

    @staticmethod
    def parse_search(stdout: str) -> list:
        ids = []
        for line in stdout.splitlines():
            name = line.strip()
            if "." not in name:  # flatpak app IDs always contain a dot
                continue
            if name not in ids:
                ids.append(name)
        return ids

    def search(self, query: str) -> list:
        proc = subprocess.run(
            ["flatpak", "search", "--columns=application", query],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            return []
        return self.parse_search(proc.stdout)

    def exists(self, package: str) -> bool:
        proc = subprocess.run(
            ["flatpak", "search", "--columns=application", package],
            capture_output=True,
            text=True,
        )
        return proc.returncode == 0 and package in proc.stdout.split()

    def install(self, packages):
        return self._run(["install", "-y", "--noninteractive"] + packages, op="install")

    def remove(self, packages):
        return self._run(["uninstall", "-y", "--noninteractive"] + packages, op="remove")

    def update(self):
        return self._run(["update", "-y", "--noninteractive"], op="update")

    def upgrade(self):
        return self.update()

    def list_installed(self) -> list:
        proc = subprocess.run(
            ["flatpak", "list", "--columns=application", "--app"],
            capture_output=True,
            text=True,
        )
        return [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]

    def info(self, package: str) -> str:
        proc = subprocess.run(["flatpak", "info", package], capture_output=True, text=True)
        return proc.stdout or "(not found)"
