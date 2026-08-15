#!/usr/bin/env bash
# ============================================================================
#  enj curl installer bootstrap
#
#  This tiny script is what the one-liner fetches. It grabs the repo and then
#  hands off to install.sh from inside it, so install.sh itself always runs
#  from the project's own files.
#
#  Usage:
#    curl -fsSL https://raw.githubusercontent.com/enjo/enj/main/curl.sh | bash
#
#  Arguments are passed straight through to install.sh, e.g.:
#    curl -fsSL URL/curl.sh | bash -s -- --yes
# ============================================================================
set -euo pipefail

REPO_URL="${ENJ_REPO:-https://github.com/enjo/enj.git}"

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

echo "▸ fetching enj from ${REPO_URL} ..."
if command -v git >/dev/null 2>&1 && git clone --depth 1 "$REPO_URL" "$tmpdir" >/dev/null 2>&1; then
  :
elif command -v curl >/dev/null 2>&1; then
  curl -fsSL "${REPO_URL%/}.git/tarball/main" -o "$tmpdir/enj.tar.gz" >/dev/null 2>&1 \
    && mkdir -p "$tmpdir/enj" \
    && tar -xzf "$tmpdir/enj.tar.gz" -C "$tmpdir/enj" --strip-components=1
fi

[ -f "$tmpdir/install.sh" ] || {
  echo "✘ failed to fetch the enj repo from $REPO_URL" >&2
  exit 1
}

echo "✔ repo fetched, running install.sh ..."
bash "$tmpdir/install.sh" --source="$tmpdir" "$@"
