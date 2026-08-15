"""emerge (portage) - Gentoo."""

from __future__ import annotations

import subprocess

from enj.managers.base import BaseManager


class EmergeManager(BaseManager):
    name = "emerge"
    display_name = "emerge (Gentoo)"
    binary = "emerge"
    native = True
    priority = 10

    SERVER = "https://mirrors.gentoo.org"
    sudo_ops = ("install", "remove", "update", "upgrade")

    @staticmethod
    def parse_search(stdout: str) -> list:
        names = []
        for line in stdout.splitlines():
            for token in line.split():
                if "/" in token and not token.startswith(("*", "(", ")")):
                    name = token.strip()
                    if name not in names:
                        names.append(name)
        return names

    def search(self, query: str) -> list:
        proc = subprocess.run(["emerge", "-S", query], capture_output=True, text=True)
        if proc.returncode not in (0, 1):
            return []
        return self.parse_search(proc.stdout)

    def exists(self, package: str) -> bool:
        return package in self.search(package)

    def install(self, packages):
        return self._run(["--ask", "n"] + packages, op="install")

    def remove(self, packages):
        return self._run(["--unmerge", "--ask", "n"] + packages, op="remove")

    def update(self):
        return self._run(["--sync"], op="update")

    def upgrade(self):
        return self._run(["-uDN", "@world"], op="upgrade")

    def list_installed(self) -> list:
        proc = self._sh(["qlist", "-I"])
        if proc.returncode == 0:
            return [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
        proc = self._run(["--query", "installed"], op=None, stream=False, check=False)
        return [ln.split()[0] for ln in proc.stdout.splitlines() if ln.strip()]

    def info(self, package: str) -> str:
        proc = self._sh(["emerge", "-S", package])
        return proc.stdout or "(not found)"
