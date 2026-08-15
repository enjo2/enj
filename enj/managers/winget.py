"""winget - the Windows Package Manager."""

from __future__ import annotations

import subprocess

from enj.managers.base import BaseManager


class WingetManager(BaseManager):
    name = "winget"
    display_name = "winget (Windows)"
    binary = "winget"
    native = False
    priority = 10

    SERVER = "https://cdn.winget.microsoft.com"
    sudo_ops = ()

    @staticmethod
    def parse_search(stdout: str) -> list:
        ids = []
        for line in stdout.splitlines():
            parts = line.split()
            if len(parts) < 3:
                continue
            if line.startswith("Name") or set(line.strip()) == {"-"}:
                continue
            ident = parts[1]
            if "." in ident and ident not in ids:
                ids.append(ident)
        return ids

    def search(self, query: str) -> list:
        proc = subprocess.run(
            ["winget", "search", "--accept-source-agreements", query],
            capture_output=True,
            text=True,
        )
        if proc.returncode not in (0, 1):
            return []
        return self.parse_search(proc.stdout)

    def exists(self, package: str) -> bool:
        proc = subprocess.run(
            ["winget", "search", "--accept-source-agreements", "--exact", "--id", package],
            capture_output=True,
            text=True,
        )
        return proc.returncode == 0

    def install(self, packages):
        args = ["install", "--accept-source-agreements", "--accept-package-agreements"]
        for p in packages:
            args += ["--id", p]
        return self._run(args, op="install")

    def remove(self, packages):
        args = ["uninstall", "--accept-source-agreements"]
        for p in packages:
            args += ["--id", p]
        return self._run(args, op="remove")

    def update(self):
        return self._run(["source", "update"], op="update")

    def upgrade(self):
        return self._run(
            ["upgrade", "--all", "--accept-source-agreements", "--accept-package-agreements"],
            op="upgrade",
        )

    def list_installed(self) -> list:
        proc = self._run(["list", "--accept-source-agreements"], op=None, stream=False, check=False)
        names = []
        for line in proc.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 2 and parts[0] not in ("Name", "Installed", "-"):
                names.append(parts[0])
        return names

    def info(self, package: str) -> str:
        proc = self._run(
            ["show", "--accept-source-agreements", "--id", package],
            op=None,
            stream=False,
            check=False,
        )
        return proc.stdout or proc.stderr or "(not found)"
