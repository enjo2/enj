"""apk - Alpine Linux."""

from __future__ import annotations

import subprocess

from enj.managers.base import BaseManager


class ApkManager(BaseManager):
    name = "apk"
    display_name = "apk (Alpine)"
    binary = "apk"
    native = True
    priority = 10

    SERVER = "https://dl-cdn.alpinelinux.org/alpine"
    sudo_ops = ("install", "remove", "update", "upgrade")

    def search(self, query: str) -> list:
        proc = subprocess.run(["apk", "search", "-d", query], capture_output=True, text=True)
        if proc.returncode != 0:
            return []
        return [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]

    def exists(self, package: str) -> bool:
        proc = subprocess.run(["apk", "search", "-e", package], capture_output=True, text=True)
        return proc.returncode == 0 and bool(proc.stdout.strip())

    def install(self, packages):
        return self._run(["add"] + packages, op="install")

    def remove(self, packages):
        return self._run(["del"] + packages, op="remove")

    def update(self):
        return self._run(["update"], op="update")

    def upgrade(self):
        return self._run(["upgrade", "-a"], op="upgrade")

    def list_installed(self) -> list:
        proc = self._run(["info"], op=None, stream=False)
        return [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]

    def info(self, package: str) -> str:
        proc = self._sh(["apk", "info", package])
        return proc.stdout or "(not found)"
