"""enj command-line interface."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional, Tuple

from enj import __version__
from enj.config import config_path, load_config, save_config
from enj.managers import by_name, discover, native_manager
from enj.osdetect import native_manager_name
from enj.speed import measure as measure_speed


class Context:
    def __init__(self, dry_run: bool = False, verbose: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.config = load_config()
        base_ctx = {
            "dry_run": dry_run or self.config.get("dry_run", False),
            "noninteractive": self.config.get("noninteractive", False),
        }
        self.managers = discover(self.config, context=base_ctx)
        self.native = native_manager(self.managers)
        self.native_name = native_manager_name()

    def manager_named(self, name: str):
        return by_name(self.managers, name)


# ---------------------------------------------------------------------------
# helpers


def _pick(ctx: Context, prompt: str, options: List[str], default: int = 0) -> int:
    """Interactive choice; falls back to the default when non-interactive."""
    if (
        ctx.dry_run
        or ctx.config.get("noninteractive")
        or not sys.stdin.isatty()
    ):
        return default
    print(prompt)
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")
    while True:
        try:
            raw = input("choice (Enter for default) > ")
        except (EOFError, KeyboardInterrupt):
            print()
            return default
        if not raw.strip():
            return default
        try:
            n = int(raw.strip())
        except ValueError:
            print("enter a number")
            continue
        if 1 <= n <= len(options):
            return n - 1
        print(f"enter a number between 1 and {len(options)}")


def _candidates(ctx: Context, pkg: str) -> List[Tuple]:
    """Search every non-native manager for a package.

    Returns a list of (manager, list_of_matches).
    """
    found = []
    for m in ctx.managers:
        if m is ctx.native:
            continue
        if m.name == "aur" and ctx.native_name not in ("pacman", "manjaro"):
            continue
        if not m.searchable():
            continue
        try:
            matches = m.search(pkg)
        except Exception as exc:  # network/repo failures shouldn't kill the flow
            if ctx.verbose:
                print(f"enj: {m.name} search failed: {exc}", file=sys.stderr)
            continue
        if matches:
            found.append((m, matches))
    return found


def _rank_by_speed(managers) -> list:
    """Rank managers by measured latency of their repository server (fastest first).

    Managers without a measurable server go last, keeping their original order.
    """
    ranked = []
    for m in managers:
        try:
            url = m.server()
        except Exception:
            url = None
        ms = None
        if url:
            try:
                ms = measure_speed(url)
            except Exception:
                ms = None
        ranked.append((m, ms))
    fast = sorted([r for r in ranked if r[1] is not None], key=lambda r: r[1])
    slow = [r for r in ranked if r[1] is None]
    return fast + slow


def _best_match(m, query: str, matches: List[str]) -> str:
    """Prefer an exact package name match; otherwise the first search hit."""
    for name in matches:
        if name.lower() == query.lower():
            return name
    try:
        if m.exists(query):
            return query
    except Exception:
        pass
    return matches[0]


def find_provider(ctx: Context, pkg: str, via: Optional[str] = None, fastest: bool = False) -> Tuple:
    """Decide which manager installs `pkg` (native first, then fallbacks).

    With `fastest`, candidates are re-ranked by live server latency and the
    quickest one wins.
    """
    if via:
        m = ctx.manager_named(via)
        if m is None:
            sys.exit(f"enj: manager '{via}' is not available on this system")
        matches = m.search(pkg)
        if not matches:
            sys.exit(f"enj: '{pkg}' not found via {m.display_name}")
        return m, _best_match(m, pkg, matches)

    if fastest:
        candidates = []
        if ctx.native and ctx.native.exists(pkg):
            candidates.append(ctx.native)
        for m, matches in _candidates(ctx, pkg):
            if m not in candidates:
                candidates.append(m)
        if not candidates:
            return None, None
        ranked = _rank_by_speed(candidates)
        m = ranked[0][0]
        if ctx.verbose:
            for m2, ms in ranked:
                tag = f"{ms:.0f} ms" if ms is not None else "unreachable"
                print(f"enj:   {m2.display_name:20} {tag}")
        if m is ctx.native:
            return m, pkg
        return m, _best_match(m, pkg, m.search(pkg))

    if ctx.native and ctx.native.exists(pkg):
        return ctx.native, pkg

    found = _candidates(ctx, pkg)
    if not found:
        return None, None

    if len(found) == 1:
        m, matches = found[0]
        return m, _best_match(m, pkg, matches)

    options = [f"{m.display_name}: {_best_match(m, pkg, matches)}" for m, matches in found]
    idx = _pick(ctx, f"'{pkg}' is available through multiple managers:", options)
    m, matches = found[idx]
    return m, _best_match(m, pkg, matches)


# ---------------------------------------------------------------------------
# subcommands


def cmd_install(args, ctx: Context) -> int:
    failed = False
    fastest = args.fastest or ctx.config.get("fastest_server", False)
    for pkg in args.packages:
        m, target = find_provider(ctx, pkg, via=args.via, fastest=fastest)
        if m is None:
            print(
                f"enj: '{pkg}' not found in any available package manager"
                f" (native={ctx.native_name or 'none'}, checked "
                f"{len(ctx.managers)} managers)",
                file=sys.stderr,
            )
            failed = True
            continue
        print(f"enj: installing '{target}' via {m.display_name}")
        if m.install([target]) != 0:
            failed = True
    return 1 if failed else 0


def cmd_remove(args, ctx: Context) -> int:
    failed = False
    for pkg in args.packages:
        target = None
        for m in ctx.managers:
            try:
                installed = m.list_installed()
            except Exception:
                continue
            if pkg in installed:
                target = m
                break
        if target is None:
            print(f"enj: '{pkg}' is not installed via any available manager", file=sys.stderr)
            failed = True
            continue
        print(f"enj: removing '{pkg}' via {target.display_name}")
        if target.remove([pkg]) != 0:
            failed = True
    return 1 if failed else 0


def cmd_search(args, ctx: Context) -> int:
    found_any = False
    for m in ctx.managers:
        if args.via and m.name != args.via:
            continue
        try:
            matches = m.search(args.query)
        except Exception as exc:
            if ctx.verbose:
                print(f"enj: {m.name} search failed: {exc}", file=sys.stderr)
            continue
        if not matches:
            continue
        found_any = True
        print(f"[{m.name}]")
        for name in matches[: args.limit]:
            print(f"  {name}")
    if not found_any:
        print(f"enj: no matches for '{args.query}'", file=sys.stderr)
        return 1
    return 0


def cmd_info(args, ctx: Context) -> int:
    m, target = find_provider(ctx, args.package, via=args.via)
    if m is None:
        print(f"enj: '{args.package}' not found", file=sys.stderr)
        return 1
    print(f"{m.display_name} :: {target}")
    try:
        print(m.info(target))
    except Exception as exc:
        print(f"(no info: {exc})", file=sys.stderr)
    return 0


def cmd_update(args, ctx: Context) -> int:
    for m in ctx.managers:
        if args.via and m.name != args.via:
            continue
        if not m.searchable():
            continue
        print(f"enj: updating {m.display_name} ...")
        try:
            m.update()
        except NotImplementedError:
            pass
        except Exception as exc:
            print(f"enj: {m.name} update failed: {exc}", file=sys.stderr)
        print(f"enj: upgrading {m.display_name} ...")
        try:
            m.upgrade()
        except NotImplementedError:
            pass
        except Exception as exc:
            print(f"enj: {m.name} upgrade failed: {exc}", file=sys.stderr)
    return 0


def cmd_upgrade(args, ctx: Context) -> int:
    for m in ctx.managers:
        if args.via and m.name != args.via:
            continue
        if not m.searchable():
            continue
        print(f"enj: upgrading {m.display_name} ...")
        try:
            m.upgrade()
        except NotImplementedError:
            pass
        except Exception as exc:
            print(f"enj: {m.name} upgrade failed: {exc}", file=sys.stderr)
    return 0


def cmd_list(args, ctx: Context) -> int:
    for m in ctx.managers:
        if args.via and m.name != args.via:
            continue
        try:
            installed = m.list_installed()
        except (NotImplementedError, Exception):
            continue
        if not installed:
            continue
        print(f"[{m.name}] ({len(installed)} installed)")
        for p in installed[: args.limit]:
            print(f"  {p}")
        if len(installed) > args.limit:
            print(f"  ... {len(installed) - args.limit} more")
    return 0


def cmd_config(args, ctx: Context) -> int:
    print(f"config file: {config_path()}")
    print(f"detected native manager: {ctx.native_name or 'none'}")
    print(f"available managers: {', '.join(m.name for m in ctx.managers) or 'none'}")
    print(f"prefix: {ctx.config.get('prefix') or '(default)'}")
    if args.write is not None:
        path = save_config(args.write)
        print(f"wrote config to {path}")
    return 0


# ---------------------------------------------------------------------------
# entry point


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="enj",
        description="Cross-platform meta package manager. Tries your system's "
        "native package manager first, then flatpak/snap/AUR/brew/... as fallbacks.",
    )
    p.add_argument("-v", "--version", action="version", version=f"enj {__version__}")
    p.add_argument("--verbose", action="store_true", help="show extra detail")
    p.add_argument("--dry-run", action="store_true", help="print commands without running them")
    sub = p.add_subparsers(dest="command", required=True)

    pi = sub.add_parser("install", aliases=["i"], help="install packages")
    pi.add_argument("packages", nargs="+")
    pi.add_argument("--via", metavar="MANAGER", help="force a specific manager (apt, pacman, flatpak, aur, ...)")
    pi.add_argument("--fastest", action="store_true", help="measure each candidate's server and install via the fastest one")
    pi.set_defaults(func=cmd_install)

    pr = sub.add_parser("remove", aliases=["r", "uninstall"], help="remove installed packages")
    pr.add_argument("packages", nargs="+")
    pr.set_defaults(func=cmd_remove)

    ps = sub.add_parser("search", aliases=["s"], help="search for packages in every available manager")
    ps.add_argument("query")
    ps.add_argument("--limit", type=int, default=None, help="max results per manager")
    ps.add_argument("--via", metavar="MANAGER", help="only search this manager")
    ps.set_defaults(func=cmd_search)

    pi2 = sub.add_parser("info", aliases=["show"], help="show package info")
    pi2.add_argument("package")
    pi2.add_argument("--via", metavar="MANAGER")
    pi2.set_defaults(func=cmd_info)

    pu = sub.add_parser("update", help="refresh indexes and upgrade all packages (all managers)")
    pu.add_argument("--via", metavar="MANAGER")
    pu.set_defaults(func=cmd_update)

    pg = sub.add_parser("upgrade", help="upgrade installed packages (all managers)")
    pg.add_argument("--via", metavar="MANAGER")
    pg.set_defaults(func=cmd_upgrade)

    pl = sub.add_parser("list", aliases=["l"], help="list installed packages (all managers)")
    pl.add_argument("--limit", type=int, default=50)
    pl.add_argument("--via", metavar="MANAGER")
    pl.set_defaults(func=cmd_list)

    pc = sub.add_parser("config", help="show or write the enj configuration")
    pc.add_argument("--write", type=str, metavar="JSON", help="write this JSON config and exit")
    pc.set_defaults(func=cmd_config)

    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    limit = getattr(args, "limit", None)
    if limit is None and args.command in ("search", "s"):
        args.limit = load_config().get("search_limit", 25)

    ctx = Context(dry_run=args.dry_run, verbose=args.verbose)
    if not ctx.managers:
        print("enj: no supported package managers found on this system", file=sys.stderr)
        return 1

    return args.func(args, ctx)
