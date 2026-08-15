# enj — the meta package manager

[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platforms](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey.svg)]()

`enj` installs software from wherever it's available — one command, any OS.

It checks your **native package manager** first (`apt`, `dnf`, `pacman`, `zypper`, …).
If the package isn't there, it falls back to whatever else is installed:
`flatpak`, AUR (`paru`/`yay`), `snap`, Homebrew, MacPorts, `nix`, `winget`,
Chocolatey, Scoop, and more. No root needed, no third-party dependencies.

```
$ enj install firefox
enj: installing 'firefox' via pacman (Arch)

$ enj install some-aur-pkg
enj: installing 'some-aur-pkg' via AUR

$ enj search "video editor"
flatpak  org.kde.kdenlive            Kdenlive - Free open source video editor
aur      kdenlive                     (AUR) Kdenlive
```

## Quick install

```sh
curl -fsSL https://raw.githubusercontent.com/enjo2/enj/main/install.sh | bash
```

The installer detects your OS/distro, walks you through choosing an install
location, and makes sure you have a good fallback manager (`flatpak` on Linux,
Homebrew on macOS, `winget` on Windows).

**Options**

```sh
bash <(curl -fsSL .../install.sh) --yes           # non-interactive
bash <(curl -fsSL .../install.sh) --prefix=/usr/local
bash <(curl -fsSL .../install.sh) --no-deps       # skip fallback manager setup
```

### Per-OS notes

| OS | Install location | Fallback manager | After install |
|---|---|---|---|
| Linux | `~/bin`, `/usr/local/bin`, `~/.local/bin` | `flatpak` | add dir to `PATH` (see below) |
| macOS | `~/bin`, `/usr/local/bin` | Homebrew (`brew`) | add dir to `PATH` |
| Windows | `%LOCALAPPDATA%\Programs` | `winget` | adds itself to `PATH`; restart terminal |

On **Linux/macOS** the installer edits your shell config automatically (table
below). On **Windows**, `winget`/`choco`/`scoop` register themselves — just
restart the terminal or PowerShell.

**Manual**

```sh
git clone https://github.com/enjo2/enj.git
cd enj
pip install -e .
```

Requires Python 3.9+. No third-party dependencies.

### PATH setup

After installing, `enj` runs from the location you chose (e.g. `~/bin/enj`).
If that directory isn't already on your `PATH`, the installer appends it to
your shell config automatically — or tells you what to run if your rc file
doesn't exist yet:

| Shell | Config file | Line added |
|---|---|---|
| zsh | `~/.zshrc` | `export PATH="/home/enjo/bin:$PATH"` |
| bash | `~/.bashrc` | `export PATH="/home/enjo/bin:$PATH"` |
| fish | `~/.config/fish/config.fish` | `fish_add_path /home/enjo/bin` |
| nushell | `~/.config/nushell/env.nu` | `$env.PATH = ($env.PATH \| prepend "/home/enjo/bin")` |
| ksh | `~/.kshrc` | `export PATH="/home/enjo/bin:$PATH"` |
| tcsh | `~/.tcshrc` | `setenv PATH "/home/enjo/bin:$PATH"` |

> **zsh note**: older shells and non-login zsh sessions may not pick up the
> change until you restart the terminal or run `source ~/.zshrc`. If `zsh:
> command not found: enj` still shows, it means `~/bin` isn't in `PATH` yet —
> either `source ~/.zshrc` or open a new terminal.

If the installer couldn't find your rc file, add the line manually for your
shell from the table above.

## Features

- **Native-first fallback** — asks your OS's own package manager before anything else.
- **Fastest-server install** — `enj install <pkg> --fastest` benchmarks each candidate's
  repository server and installs via the quickest one.
- **Unified interface** — the same `install`/`remove`/`search`/`info`/`update` for 16+ managers.
- **Cross-platform** — Debian→Arch→macOS→Windows, same commands everywhere.
- **Best-manager install** — `install.sh` auto-installs the recommended fallback per OS.
- **Dry-run** — `enj --dry-run install vim` shows exactly what would run, without doing it.
- **Per-manager override** — `enj install firefox --via flatpak`.
- **Configurable** — enable/disable managers, set fallback priority, search limits.

## Usage

| Command | What it does |
|---|---|
| `enj install <pkg>…` | Native manager first, then fallback chain. Prompts if several managers provide it. |
| `enj install <pkg> --via flatpak` | Force a specific manager. |
| `enj install <pkg> --fastest` | Measure each candidate's server and install via the fastest one. |
| `enj remove <pkg>…` | Uninstalls from whichever manager has it installed. |
| `enj search <query>` | Searches every available manager at once. |
| `enj info <pkg>` | Shows package details. |
| `enj update` | Refreshes indexes **and** upgrades all packages (all managers). |
| `enj upgrade` | Upgrades everything (all managers). |
| `enj list` | Lists installed packages grouped by manager. |
| `enj config` | Shows config path, detected native manager, available managers. |
| `enj --dry-run install <pkg>` | Print what would run without doing it. |

## How the fallback works

1. Detect the OS/distro from `/etc/os-release` (or `platform` on macOS/Windows).
2. Ask the **native manager** — exact name match in its official repos.
3. Not found? `search()` every available fallback manager and collect matches.
4. One match → install it. Several matches → pick interactively (first by default).
5. `--fastest` → benchmark each candidate's repository server (TCP handshake,
   ~50 ms each) and install via the quickest one. Nothing → error.

```
                     ┌──────────────┐
   enj install X ───▶│ native pm?   │── yes ──▶ install via native
                     └──────┬──────┘
                        no  ▼
                  ┌───────────────────┐
                  │ scan fallbacks:   │
                  │ flatpak snap aur  │── one match ──▶ install
                  │ brew macports nix │
                  │ winget choco scoop│── several ─────▶ choose
                  └───────────────────┘
```

## Supported managers

| Manager | OS | Role |
|---|---|---|
| apt | Debian/Ubuntu | native |
| dnf | Fedora/RHEL/Rocky | native |
| pacman | Arch/Manjaro | native |
| zypper | openSUSE | native |
| apk | Alpine | native |
| emerge | Gentoo | native |
| xbps | Void | native |
| nix | NixOS / any | native or fallback |
| brew | macOS / Linux | native on macOS, fallback elsewhere |
| macports | macOS | fallback |
| flatpak | Linux | fallback |
| snap | Linux | fallback |
| aur (paru/yay) | Arch | fallback |
| winget | Windows | default |
| choco | Windows | fallback |
| scoop | Windows | fallback |

## Configuration

`~/.config/enj/config.json`:

```json
{
  "managers": {
    "enabled": ["pacman", "flatpak", "aur"],
    "disabled": ["snap"],
    "priority": { "flatpak": 10, "snap": 20, "aur": 15 }
  },
  "search_limit": 25,
  "noninteractive": false,
  "dry_run": false,
  "fastest_server": false
}
```

- `enabled` restricts enj to those managers.
- `priority` controls the order fallbacks are offered (lower = tried first).
- `fastest_server` makes every `enj install` behave like `--fastest`.
- `dry_run` makes every command print-only.

## Development

```sh
pip install -e .
python -m unittest discover -s tests
```

## Architecture

```
enj/
├── install.sh               # curl installer: TUI, OS detection, prereqs, PATH setup
├── enj/
│   ├── cli.py               # subcommands & output
│   ├── config.py            # ~/.config/enj/config.json
│   ├── osdetect.py          # OS/distro → native manager
│   ├── speed.py             # server latency measurement (--fastest)
│   └── managers/
│       ├── base.py          # PackageManager interface + Provider
│       ├── __init__.py      # registry + discover() (native first)
│       ├── apt.py dnf.py pacman.py zypper.py apk.py emerge.py xbps.py nix.py
│       ├── flatpak.py snap.py aur.py brew.py macports.py
│       └── winget.py chocolatey.py scoop.py
└── tests/
    └── test_core.py         # distro mapping + search parsing
```

Adding a new package manager = a new small module in `enj/managers/` implementing
the `PackageManager` interface. That's it.

## License

MIT
