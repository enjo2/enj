"""Configuration handling. Config lives at ~/.config/enj/config.json."""

from __future__ import annotations

import json
import os
from typing import Any

DEFAULTS = {
    "managers": {
        # restrict enj to only these managers (empty = all found on the system)
        "enabled": [],
        # never use these managers even if installed
        "disabled": [],
        # per-manager priority (lower = tried first among fallbacks)
        "priority": {"flatpak": 10, "aur": 15, "snap": 20, "brew": 30, "nix": 40},
    },
    "search_limit": 25,
    "noninteractive": False,
    "dry_run": False,
    "fastest_server": False,
    # default install prefix for package operations (set by the installer)
    "prefix": "",
}


def config_dir() -> str:
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(base, "enj")


def config_path() -> str:
    return os.path.join(config_dir(), "config.json")


def _merge(base: dict, over: dict) -> dict:
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _merge(base[k], v)
        else:
            base[k] = v
    return base


def load_config() -> dict:
    cfg = json.loads(json.dumps(DEFAULTS))
    try:
        with open(config_path(), encoding="utf-8") as f:
            user = json.load(f)
    except (OSError, json.JSONDecodeError):
        return cfg
    return _merge(cfg, user)


def save_config(cfg: dict) -> str:
    os.makedirs(config_dir(), exist_ok=True)
    path = config_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
        f.write("\n")
    return path
