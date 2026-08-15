"""dnf - Fedora / RHEL / CentOS and derivatives."""

from __future__ import annotations

import subprocess

from enj.managers.base import BaseManager


class DnfManager(BaseManager):
    name = "dnf"
    display_name = "dnf (Fedora/RHEL)"
    binary = "dnf"
    native = True
    priority = 20
    sudo_ops = ("install", "remove", "update", "upgrade")

    @staticmethod
    def parse_search(stdout: str) -> list:
        names = []
        for line in stdout.splitlines():
            if " : " in line:
                name = line.split(" : ", 1)[0].strip()
                if name and name not in names:
                    names.append(name)
        return names

    def search(self, query: str) -> list:
        proc = subprocess.run(["dnf", "search", query], capture_output=True, text=True)
        if proc.returncode not in (0, 1):
            return []
        return self.parse_search(proc.stdout)

    def exists(self, package: str) -> bool:
        proc = subprocess.run(["dnf", "list", "available", package], capture_output=True, text=True)
        return proc.returncode == 0 and package in proc.stdout

    def install(self, packages):
        return self._run(["install", "-y"] + packages, op="install")

    def remove(self, packages):
        return self._run(["remove", "-y"] + packages, op="remove")

    def update(self):
        return self._run(["makecache"], op="update")

    def upgrade(self):
        return self._run(["upgrade", "-y"], op="upgrade")

    def list_installed(self) -> list:
        proc = self._run(["list", "--installed"], op=None, stream=False)
        names = []
        started = False
        for line in proc.stdout.splitlines():
            if line.strip() == "Installed Packages":
                started = True
                continue
            if started and line.strip():
                name = line.split()[0]
                if "." in name:
                    name = name.rsplit(".", 1)[0]
                names.append(name)
        return names

    def info(self, package: str) -> str:
        proc = self._sh(["dnf", "info", package])
        return proc.stdout or "(not found)"

    def server(self) -> str:
        import glob

        for path in glob.glob("/etc/yum.repos.d/*.repo"):
            try:
                with open(path, encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line = line.strip()
                        if line.lower().startswith("baseurl="):
                            url = line.split("=", 1)[1].strip().split()[0]
                            if "://" in url:
                                return url
            except OSError:
                continue
        return "https://mirrors.fedoraproject.org"
