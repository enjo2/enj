"""nix - NixOS / Nix package manager."""

from __future__ import annotations

import shutil
import subprocess

from enj.managers.base import BaseManager


class NixManager(BaseManager):
    name = "nix"
    display_name = "nix"
    binary = "nix-env"
    native = True
    priority = 10
    sudo_ops = ()  # nix-env operates on the user profile, no root needed

    @staticmethod
    def parse_search(stdout: str) -> list:
        names = []
        for line in stdout.splitlines():
            if not line.strip():
                continue
            token = line.split()[0]
            if ":" in token:
                token = token.split(":", 1)[1]
            if "." in token:
                token = token.split(".", 1)[1]
            if token and token not in names:
                names.append(token)
        return names

    def _query(self, query: str):
        if shutil.which("nix"):
            proc = subprocess.run(
                ["nix", "search", "nixpkgs", query], capture_output=True, text=True
            )
            if proc.returncode == 0:
                return proc.stdout
        proc = subprocess.run(
            ["nix-env", "-qaP", query], capture_output=True, text=True
        )
        return proc.stdout

    def search(self, query: str) -> list:
        return self.parse_search(self._query(query))

    def exists(self, package: str) -> bool:
        return package in self.parse_search(self._query(package))

    def install(self, packages):
        args = []
        for p in packages:
            args += ["-iA", f"nixpkgs.{p}"]
        return self._run(args, op="install")

    def remove(self, packages):
        return self._run(["-e"] + packages, op="remove")

    def update(self):
        if shutil.which("nix-channel"):
            return subprocess.call(["nix-channel", "--update"])
        return 0

    def upgrade(self):
        return self._run(["-u"], op="upgrade")

    def list_installed(self) -> list:
        proc = self._run(["-q"], op=None, stream=False)
        return [ln.split()[0] for ln in proc.stdout.splitlines() if ln.strip()]

    def info(self, package: str) -> str:
        proc = subprocess.run(["nix-env", "-qaP", package], capture_output=True, text=True)
        return proc.stdout or "(not found)"
