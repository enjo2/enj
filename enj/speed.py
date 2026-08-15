"""Server latency measurement, used to pick the fastest package source.

Pure stdlib: TCP connect time is a good proxy for how fast a package
repository will be, and it avoids downloading large index files.
"""

from __future__ import annotations

import socket
import time
import urllib.parse
from typing import List, Optional, Tuple

DEFAULT_TIMEOUT = 3.0


def measure_connect(host: str, port: int = 443, timeout: float = DEFAULT_TIMEOUT) -> Optional[float]:
    """TCP handshake time to (host, port) in milliseconds, or None on failure."""
    try:
        start = time.monotonic()
        with socket.create_connection((host, port), timeout=timeout):
            elapsed = time.monotonic() - start
        return elapsed * 1000.0
    except OSError:
        return None


def measure(url: str, timeout: float = DEFAULT_TIMEOUT) -> Optional[float]:
    """Best-effort latency (ms) for a server URL, using the connect handshake."""
    parsed = urllib.parse.urlsplit(url)
    host = parsed.hostname or url
    try:
        port = parsed.port or (443 if parsed.scheme in ("https", "wss") else 80)
    except ValueError:
        port = 443
    return measure_connect(host, port, timeout)


def pick_fastest(urls: List[str], timeout: float = DEFAULT_TIMEOUT) -> Optional[Tuple[str, float]]:
    """Return (url, ms) with the lowest measured latency; None if all are down."""
    best: Optional[Tuple[str, float]] = None
    for url in urls:
        ms = measure(url, timeout=timeout)
        if ms is None:
            continue
        if best is None or ms < best[1]:
            best = (url, ms)
    return best
