"""Base class every enj package manager implements."""

from __future__ import annotations

import shutil
import subprocess
from typing import Any, Dict, List, Optional

from enj.osdetect import is_root


class BaseManager:
    name = "base"
    display_name = "Base"
    binary: Optional[str] = None
    native = False
    priority = 100
    sudo_ops = ()  # which operations need root: e.g. ("install", "remove", ...)
    search_args = ("search",)

    def __init__(self, context: Optional[Dict[str, Any]] = None):
        self.context = context or {}

    # -- discovery ----------------------------------------------------------

    def available(self) -> bool:
        return bool(self.binary and shutil.which(self.binary))

    def searchable(self) -> bool:
        return True

    def server(self) -> Optional[str]:
        """Return the manager's primary repository server URL (for latency ranking).

        Subclasses override this when they can introspect configured mirrors.
        """
        return getattr(self, "SERVER", None)

    # -- subprocess helpers ---------------------------------------------------

    def _run(self, args, op=None, check=True, stream=None):
        cmd = [self.binary] + list(args)
        if op and op in self.sudo_ops and not is_root():
            cmd = ["sudo"] + cmd
        if self.context.get("dry_run") and op:
            print(f"[dry-run] {' '.join(cmd)}")
            return 0
        if stream is None:
            stream = op is not None
        if stream:
            return subprocess.call(cmd)
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if check and proc.returncode != 0:
            raise RuntimeError(
                f"{self.name}: command failed ({proc.returncode}): {' '.join(cmd)}"
            )
        return proc

    def _sh(self, args, check=False):
        """Run a bare command (no prefix binary) and return a CompletedProcess."""
        return subprocess.run(list(args), capture_output=True, text=True)

    # -- operations to override ----------------------------------------------

    def search(self, query: str) -> List[str]:
        raise NotImplementedError

    def exists(self, package: str) -> bool:
        raise NotImplementedError

    def install(self, packages: List[str]):
        raise NotImplementedError

    def remove(self, packages: List[str]):
        raise NotImplementedError

    def update(self):
        raise NotImplementedError

    def upgrade(self):
        raise NotImplementedError

    def list_installed(self) -> List[str]:
        raise NotImplementedError

    def info(self, package: str) -> str:
        return f"(no info available for {self.name})"
