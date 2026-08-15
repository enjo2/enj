#!/usr/bin/env bash
# ============================================================================
#  enj installer
#  A cross-platform meta package manager.
#
#  Usage:
#    curl -fsSL https://raw.githubusercontent.com/enjo2/enj/main/install.sh | bash
#
#  Options:
#    --yes | -y            skip all prompts (non-interactive)
#    --no-deps             do NOT install recommended package managers
#    --prefix=PATH         install into PATH (skips the prefix menu)
#    --source=PATH         install from a local copy of the repo (dev/testing)
#    --repo=URL            git repository to fetch (default: GitHub)
#    -h | --help           show this help
# ============================================================================
set -euo pipefail

VERSION="0.1.0"
ENJ_REPO="${ENJ_REPO:-https://github.com/enjo2/enj.git}"
SCRIPT_DIR="${BASH_SOURCE[0]:-}"
if [ -n "$SCRIPT_DIR" ]; then
  SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_DIR")" && pwd)"
fi

# ---------------------------------------------------------------------------
#  terminal setup / UI helpers
# ---------------------------------------------------------------------------
RESET=$'\033[0m'
BOLD=$'\033[1m'
DIM=$'\033[2m'
CYAN=$'\033[0;36m'
GREEN=$'\033[0;32m'
YELLOW=$'\033[0;33m'
RED=$'\033[0;31m'
MAGENTA=$'\033[0;35m'
WHITE=$'\033[1;97m'

INTERACTIVE=0
[ -e /dev/tty ] && INTERACTIVE=1

info() { printf '\033[0;37m▸\033[0m %s\n' "$*"; }
ok()   { printf '\033[0;32m✔\033[0m %s\n' "$*"; }
warn() { printf '\033[0;33m⚠\033[0m %s\n' "$*"; }
err()  { printf '\033[0;31m✘\033[0m %s\n' "$*"; }

# ---------------------------------------------------------------------------
#  ascii logo
# ---------------------------------------------------------------------------
logo() {
  if [ "${NO_COLOR:-0}" != "1" ]; then
    cat <<'EOF'
  _____        _ 
 | ____|_ __  (_)
 |  _| | '_ \ | |
 | |___| | | || |
 |_____|_| |_|/ |
            |__/ 
EOF
    printf "${DIM}%s${RESET}\n\n" $'\142\171\040\145\156\152\157'
  else
    echo "enj - the meta package manager"
    printf '%s\n' $'\142\171\040\145\156\152\157'
  fi
}

# read a single keypress from the tty
tty_input() {
  local _var="${1:-}"
  if [ "$INTERACTIVE" -eq 1 ]; then
    IFS= read -r -n1 -s -t 3600 "$_var" </dev/tty || true
  else
    eval "$_var="
  fi
}

tty_readline() {
  if [ "$INTERACTIVE" -eq 1 ]; then
    read -r -t 3600 "$@" </dev/tty || true
  fi
}

# print a line centered within the terminal width
center() {
  local cols=$(( $(tput cols 2>/dev/null || echo 80) ))
  local str="$1"
  local pad=$(( (cols - ${#str}) / 2 ))
  [ $pad -lt 0 ] && pad=0
  printf "%*s%s%s\n" "$pad" "" "$RESET" "$str"
}

# ---------------------------------------------------------------------------
#  configuration (tunable via env before running)
# ---------------------------------------------------------------------------
PREFIX="${PREFIX:-}"
YES="${YES:-0}"
NO_DEPS="${NO_DEPS:-0}"
SOURCE="${SOURCE:-}"

# supported package manager backends (runtime discovery happens in enj itself)
declare -A PM_DESC=(
  [flatpak]="universal Linux app distribution (Flathub)"
  [brew]="Homebrew - macOS & Linux package manager"
  [winget]="Windows Package Manager"
  [snap]="snap packages for Linux"
)

# ---------------------------------------------------------------------------
#  OS / distro detection
# ---------------------------------------------------------------------------
detect_os() {
  case "$(uname -s)" in
    Linux)  OS=linux; OS_NAME="Linux" ;;
    Darwin) OS=macos; OS_NAME="macOS" ;;
    MINGW*|MSYS*|CYGWIN*) OS=windows; OS_NAME="Windows" ;;
    *)      OS=linux; OS_NAME="$(uname -s)" ;;
  esac
}

detect_distro() {
  DISTRO="unknown"
  [ -r /etc/os-release ] || return 0
  # shellcheck disable=SC1091
  . /etc/os-release
  DISTRO="${ID:-unknown}"
  DISTRO_NAME="${PRETTY_NAME:-$DISTRO}"
  case "$DISTRO" in
    ubuntu|debian)   NATIVE_MANAGER="apt" ;;
    fedora|rhel|rocky|almalinux|centos) NATIVE_MANAGER="dnf" ;;
    arch|manjaro|endeavouros) NATIVE_MANAGER="pacman" ;;
    opensuse*|sles)  NATIVE_MANAGER="zypper" ;;
    alpine)          NATIVE_MANAGER="apk" ;;
    gentoo)          NATIVE_MANAGER="emerge" ;;
    void)            NATIVE_MANAGER="xbps" ;;
    nixos)           NATIVE_MANAGER="nix" ;;
    *)               NATIVE_MANAGER="" ;;
  esac
}

# ---------------------------------------------------------------------------
#  argument parsing
# ---------------------------------------------------------------------------
usage() {
  cat <<'EOF'
enj installer v0.1.0

Options:
  --yes | -y            skip all prompts (non-interactive)
  --no-deps             do NOT install recommended package managers
  --prefix=PATH         install into PATH (skips the prefix menu)
  --source=PATH         install from a local copy of the repo (dev/testing)
  --repo=URL            git repository to fetch
  -h | --help           show this help

Examples:
  curl -fsSL URL/install.sh | bash
  curl -fsSL URL/install.sh | bash -s -- --yes
  bash install.sh --prefix=$HOME/.local
EOF
}

parse_args() {
  for arg in "$@"; do
    case "$arg" in
      --yes|-y)         YES=1 ;;
      --no-deps)        NO_DEPS=1 ;;
      --prefix=*)       PREFIX="${arg#--prefix=}" ;;
      --source=*)       SOURCE="${arg#--source=}" ;;
      --repo=*)         ENJ_REPO="${arg#--repo=}" ;;
      -h|--help)        usage; exit 0 ;;
      *)                warn "unknown option: $arg" ;;
    esac
  done
}

# ---------------------------------------------------------------------------
#  TUI: pick a prefix
# ---------------------------------------------------------------------------
prefix_menu() {
  local -a opts=(
    "$HOME/bin"
    "/usr/local/bin"
    "$HOME/.local/bin"
  )
  local -a desc=(
    "user install, no root required (recommended)"
    "system-wide install (requires sudo)"
    "simple, no root required"
  )
  local count=${#opts[@]}
  local selected=0
  local key

  if ! command -v tput >/dev/null 2>&1; then
    warn "terminal UI unavailable, using $HOME/.local"
    PREFIX_DIR="$HOME/.local"
    return 0
  fi

  printf "\n%s%s choose an install location:%s\n\n" "$BOLD" "$CYAN" "$RESET"
  while true; do
    for i in "${!opts[@]}"; do
      if [ "$i" -eq "$selected" ]; then
        printf "%s  ${WHITE}${BOLD}▶ ${opts[$i]}${RESET}  ${DIM}${desc[$i]}${RESET}\n"
      else
        printf "    ${DIM}${opts[$i]}${RESET}  ${DIM}${desc[$i]}${RESET}\n"
      fi
    done
    printf "\n  ${DIM}↑/↓ navigate   ↵ select   q quit${RESET}\n"
    tty_input key
    case "$key" in
      $'\x1b')
        read -r -n2 -s -t 0.1 </dev/tty || true
        case "$REPLY" in
          "[A") selected=$(( (selected - 1 + count) % count )) ;;
          "[B") selected=$(( (selected + 1) % count )) ;;
        esac
        ;;
      $'\x0a'|"") PREFIX_DIR="${opts[$selected]}"; return 0 ;;
      "q") exit 1 ;;
    esac
    printf "\033[%sA\033[J" "$((count + 2))"
  done
}

# ---------------------------------------------------------------------------
#  TUI: pick a command name
# ---------------------------------------------------------------------------
name_prompt() {
  local default="enj"
  printf "\n%s%s choose a command name [%s]:%s " "$BOLD" "$CYAN" "$default" "$RESET"
  if [ "$YES" -eq 1 ]; then
    NAME="$default"
  else
    NAME="$default"
    read -r NAME < /dev/tty || NAME="$default"
    if [ -z "$NAME" ]; then NAME="$default"; fi
  fi
}

# ---------------------------------------------------------------------------
#  prerequisite package managers
# ---------------------------------------------------------------------------
have() { command -v "$1" >/dev/null 2>&1; }

recommended_manager() {
  case "$OS" in
    linux)   echo "flatpak" ;;
    macos)   echo "brew" ;;
    windows) echo "winget" ;;
  esac
}

run_as_root() {
  if [ "$(id -u)" -eq 0 ]; then
    "$@"
  elif command -v sudo >/dev/null 2>&1; then
    sudo "$@"
  else
    err "need root to run: $*"
    return 1
  fi
}

install_brew() {
  if ! have brew; then
    warn "Homebrew not found - recommended manager for ${OS}."
    if [ "$YES" -eq 1 ]; then
      NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    else
      info "installing Homebrew now (official script) ..."
      /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
  else
    ok "Homebrew already installed"
  fi
}

install_flatpak() {
  if have flatpak; then
    ok "flatpak already installed"
    return 0
  fi
  warn "flatpak not found - enj uses it as a fallback manager on Linux."
  info "install it with your native package manager, e.g.:"
  case "$NATIVE_MANAGER" in
    apt)    info "  sudo apt install flatpak" ;;
    dnf)    info "  sudo dnf install flatpak" ;;
    pacman) info "  sudo pacman -S --noconfirm flatpak" ;;
    zypper) info "  sudo zypper install flatpak" ;;
    *)      info "  flatpak (via ${NATIVE_MANAGER:-your distro package manager})" ;;
  esac
  if [ "$YES" -eq 1 ] && [ -n "$NATIVE_MANAGER" ]; then
    case "$NATIVE_MANAGER" in
      apt)    run_as_root apt-get update -qq && run_as_root apt-get install -y flatpak ;;
      dnf)    run_as_root dnf install -y flatpak ;;
      pacman) run_as_root pacman -S --noconfirm flatpak ;;
      zypper) run_as_root zypper --non-interactive install flatpak ;;
    esac
  fi
}

install_prereqs() {
  [ "$NO_DEPS" -eq 1 ] && { info "skipping recommended manager install (--no-deps)"; return 0; }
  case "$OS" in
    linux)   install_flatpak ;;
    macos)   install_brew ;;
    windows) have winget && ok "winget already installed" || warn "winget not found - install the Windows App Installer from the Microsoft Store." ;;
  esac
}

# ---------------------------------------------------------------------------
#  main install
# ---------------------------------------------------------------------------
find_local_clone() {
  # look for an already-cloned enj repo and prefer it over a fresh clone
  local dir
  for dir in "$SCRIPT_DIR" "$PWD" "$HOME/enj" "${ENJ_SOURCE:-}"; do
    if [ -n "$dir" ] && [ -f "$dir/pyproject.toml" ] && [ -f "$dir/install.sh" ]; then
      printf '%s\n' "$dir"
      return 0
    fi
  done
  return 1
}

install_enj() {
  local src="$SOURCE" tmpdir=""
  if [ -z "$src" ]; then
    # use an already-cloned repo when we find one
    if local_dir="$(find_local_clone)"; then
      info "using existing enj repo at $local_dir"
      src="$local_dir"
    else
      tmpdir="$(mktemp -d)"
      info "cloning enj from ${ENJ_REPO} ..."
      git clone --depth 1 "$ENJ_REPO" "$tmpdir" >/dev/null 2>&1 || {
        err "failed to clone ${ENJ_REPO}"
        rm -rf "$tmpdir"
        exit 1
      }
      src="$tmpdir"
    fi
  fi

  [ -f "$src/pyproject.toml" ] || { err "not a valid enj repo: $src"; rm -rf "$tmpdir"; exit 1; }

  mkdir -p "$(dirname "$PREFIX")"
  info "installing enj into $PREFIX ..."
  if [ -n "$tmpdir" ]; then
    # temp clone: regular install (editable would break once tmpdir is removed)
    pip install --user --break-system-packages "$src" >/dev/null 2>&1 || {
      err "pip install failed - try:  pip install --user $src"
      rm -rf "$tmpdir"
      exit 1
    }
  else
    pip install --user --break-system-packages -e "$src" >/dev/null 2>&1 || {
      err "pip install failed - try:  pip install --user -e $src"
      exit 1
    }
  fi

  # the chosen prefix itself is the `enj` command, so it can be run as
  #   <your-prefix> install <app>
  cat > "$PREFIX" <<'LAUNCHER'
#!/usr/bin/env python3
import sys
from enj.cli import main

if __name__ == "__main__":
    sys.exit(main())
LAUNCHER
  chmod +x "$PREFIX"

  [ -n "$tmpdir" ] && rm -rf "$tmpdir"

  # remember the chosen prefix so enj uses it for package operations
  local cfg_dir="${XDG_CONFIG_HOME:-$HOME/.config}/enj"
  local cfg_file="$cfg_dir/config.json"
  mkdir -p "$cfg_dir"
  if [ -f "$cfg_file" ]; then
    python3 -c '
import json, sys
path, prefix = sys.argv[1], sys.argv[2]
try:
    with open(path, encoding="utf-8") as f:
        cfg = json.load(f)
except (OSError, json.JSONDecodeError):
    cfg = {}
cfg["prefix"] = prefix
with open(path, "w", encoding="utf-8") as f:
    json.dump(cfg, f, indent=2); f.write("\n")
' "$cfg_file" "$PREFIX"
  else
    cat > "$cfg_file" <<EOF
{
  "prefix": "$PREFIX"
}
EOF
  fi

  bin_dir="$(dirname "$PREFIX")"
  case ":$PATH:" in
    *":$bin_dir:"*) ;;
    *)
      info "adding $bin_dir to your PATH"
      rc=""
      rc_line=""
      case "${SHELL:-}" in
        *zsh)  rc="$HOME/.zshrc";    rc_line='export PATH="%s:$PATH"' ;;
        *bash) rc="$HOME/.bashrc";   rc_line='export PATH="%s:$PATH"' ;;
        *fish) rc="$HOME/.config/fish/config.fish"
               rc_line='fish_add_path %s' ;;
        *nu)   rc="$HOME/.config/nushell/env.nu"
               rc_line='$env.PATH = ($env.PATH | prepend "%s")' ;;
        *ksh)  rc="$HOME/.kshrc";    rc_line='export PATH="%s:$PATH"' ;;
        *tcsh) rc="$HOME/.tcshrc";   rc_line='setenv PATH "%s:$PATH"' ;;
      esac
      if [ -n "$rc" ] && [ -f "$rc" ]; then
        if [ "$(basename "$rc")" = "config.fish" ]; then
          if ! grep -qF "fish_add_path $bin_dir" "$rc"; then
            printf '\n# enj\nfish_add_path %s\n' "$bin_dir" >> "$rc"
          fi
        elif [ "$(basename "$rc")" = "env.nu" ]; then
          if ! grep -qF 'prepend "'"$bin_dir"'"' "$rc"; then
            printf '\n# enj\n$env.PATH = ($env.PATH | prepend "%s")\n' "$bin_dir" >> "$rc"
          fi
        elif [ "$(basename "$rc")" = ".tcshrc" ]; then
          if ! grep -qF "setenv PATH \"$bin_dir:\$PATH\"" "$rc"; then
            printf '\n# enj\nsetenv PATH "%s:$PATH"\n' "$bin_dir" >> "$rc"
          fi
        else
          if ! grep -qF "export PATH=\"$bin_dir:\$PATH\"" "$rc"; then
            printf '\n# enj\nexport PATH="%s:$PATH"\n' "$bin_dir" >> "$rc"
          fi
        fi
        ok "added $bin_dir to $rc"
      else
        case "${SHELL:-}" in
          *zsh)  info "  echo 'export PATH=\"$bin_dir:\$PATH\"' >> ~/.zshrc" ;;
          *bash) info "  echo 'export PATH=\"$bin_dir:\$PATH\"' >> ~/.bashrc" ;;
          *fish) info "  fish_add_path $bin_dir" ;;
          *nu)   info "  \$env.PATH = (\$env.PATH | prepend \"$bin_dir\")" ;;
          *ksh)  info "  echo 'export PATH=\"$bin_dir:\$PATH\"' >> ~/.kshrc" ;;
          *tcsh) info "  echo 'setenv PATH \"$bin_dir:\$PATH\"' >> ~/.tcshrc" ;;
          *)     info "  export PATH=\"$bin_dir:\$PATH\"" ;;
        esac
      fi
      ;;
  esac
}

# ---------------------------------------------------------------------------
#  entrypoint
# ---------------------------------------------------------------------------
main() {
  parse_args "$@"
  detect_os
  detect_distro

  logo
  case "$OS" in
    linux)   os_label="${DISTRO_NAME:-Linux}" ;;
    macos)   os_label="macOS" ;;
    windows) os_label="Windows" ;;
    *)       os_label="$OS_NAME" ;;
  esac
  printf "\n  ${DIM}installer v%s  |  %s  |  native: %s${RESET}\n\n" \
    "$VERSION" "$os_label" "${NATIVE_MANAGER:-none}"

  PREFIX="${PREFIX:-}"
  PREFIX_DIR="${PREFIX_DIR:-}"
  NAME="${NAME:-}"
  if [ -z "$PREFIX_DIR" ] && [ -z "$PREFIX" ]; then
    if [ "$YES" -eq 1 ]; then
      PREFIX_DIR="$HOME/.local"
    else
      prefix_menu
    fi
  fi
  if [ -z "$NAME" ]; then
    name_prompt
  fi
  # the command file is the chosen directory + the chosen name
  if [ -z "$PREFIX" ]; then PREFIX="${PREFIX_DIR%/}/$NAME"; fi

  install_prereqs
  install_enj

  printf "\n"
  ok "enj installed at $PREFIX"
  printf "\n${GREEN}${BOLD}  → run:  %s install <package>${RESET}\n" "$NAME"
  printf "  → help: %s --help\n\n" "$NAME"
}

main "$@"
