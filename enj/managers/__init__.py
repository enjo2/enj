"""Manager registry and discovery."""

from __future__ import annotations

from typing import Dict, List, Optional

from enj.managers.apk import ApkManager
from enj.managers.apt import AptManager
from enj.managers.aur import AurManager
from enj.managers.brew import BrewManager
from enj.managers.chocolatey import ChocolateyManager
from enj.managers.dnf import DnfManager
from enj.managers.emerge import EmergeManager
from enj.managers.flatpak import FlatpakManager
from enj.managers.macports import MacportsManager
from enj.managers.nix import NixManager
from enj.managers.pacman import PacmanManager
from enj.managers.scoop import ScoopManager
from enj.managers.snap import SnapManager
from enj.managers.winget import WingetManager
from enj.managers.xbps import XbpsManager
from enj.managers.zypper import ZypperManager
from enj.osdetect import native_manager_name

ALL_MANAGER_CLASSES = [
    AptManager,
    DnfManager,
    PacmanManager,
    ZypperManager,
    ApkManager,
    EmergeManager,
    XbpsManager,
    NixManager,
    FlatpakManager,
    SnapManager,
    AurManager,
    BrewManager,
    MacportsManager,
    WingetManager,
    ChocolateyManager,
    ScoopManager,
]


def discover(config: Optional[Dict] = None, context: Optional[Dict] = None) -> List:
    """Return all package managers present on this system, native first.

    Ordering: native managers first, then fallbacks sorted by priority.
    """
    mcfg = (config or {}).get("managers", {})
    enabled = mcfg.get("enabled") or None
    disabled = set(mcfg.get("disabled", []))
    priorities = mcfg.get("priority", {})

    managers = []
    for cls in ALL_MANAGER_CLASSES:
        if enabled is not None and cls.name not in enabled:
            continue
        if cls.name in disabled:
            continue
        m = cls(context=context or {})
        if not m.available():
            continue
        m.priority = priorities.get(cls.name, cls.priority)
        managers.append(m)

    managers.sort(key=lambda m: (0 if m.native else 1, m.priority, m.name))
    return managers


def by_name(managers: List, name: Optional[str]):
    if not name:
        return None
    for m in managers:
        if m.name == name:
            return m
    return None


def native_manager(managers: List):
    return by_name(managers, native_manager_name())
