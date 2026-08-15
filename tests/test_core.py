"""Tests for OS detection and search-output parsing (no system packages needed)."""

import unittest
from unittest.mock import patch

from enj.osdetect import NATIVE_BY_DISTRO, native_manager_name

from enj.managers.apt import AptManager
from enj.managers.dnf import DnfManager
from enj.managers.pacman import PacmanManager
from enj.managers.zypper import ZypperManager
from enj.managers.flatpak import FlatpakManager
from enj.managers.snap import SnapManager
from enj.managers.winget import WingetManager
from enj.managers.brew import BrewManager

from enj.speed import pick_fastest


class TestDistroMapping(unittest.TestCase):
    def test_known_distros(self):
        cases = {
            "arch": "pacman",
            "manjaro": "pacman",
            "ubuntu": "apt",
            "debian": "apt",
            "fedora": "dnf",
            "rhel": "dnf",
            "opensuse": "zypper",
            "alpine": "apk",
            "gentoo": "emerge",
            "void": "xbps",
            "nixos": "nix",
        }
        for distro, expected in cases.items():
            self.assertEqual(NATIVE_BY_DISTRO[distro], expected)


class TestParseSearch(unittest.TestCase):
    def test_apt(self):
        out = "firefox - Mozilla Firefox browser\nfirefox-locale-en - English locale\n"
        self.assertEqual(AptManager.parse_search(out), ["firefox", "firefox-locale-en"])

    def test_dnf(self):
        out = "===== Name Matched: htop =====\nhtop : Interactive process viewer\n===== Summary Matched =====\n"
        self.assertEqual(DnfManager.parse_search(out), ["htop"])

    def test_pacman(self):
        out = "extra/htop 3.2.2-2 (system)\n    Interactive process viewer\ncore/git 2.45.1-1 (vcs)\n    A fast scalable\n"
        self.assertEqual(PacmanManager.parse_search(out), ["htop", "git"])

    def test_zypper(self):
        out = (
            "S | Name | Type | Version | Arch | Repository\n"
            "---+------+------+---------+------+-----------\n"
            "i | htop | package | 3.1.0 | x86_64 | repo-oss\n"
        )
        self.assertEqual(ZypperManager.parse_search(out), ["htop"])

    def test_flatpak(self):
        out = "org.mozilla.firefox\norg.videolan.VLC\n"
        self.assertEqual(FlatpakManager.parse_search(out), ["org.mozilla.firefox", "org.videolan.VLC"])

    def test_snap(self):
        out = "Name  Version  Publisher  Notes\nfirefox  1.0  mozilla  classic\nhtop  3.1.0  john  classic\n"
        self.assertEqual(SnapManager.parse_search(out), ["firefox", "htop"])

    def test_winget(self):
        out = (
            "Name  Id  Version  Source\n"
            "---  ---  ---  ---\n"
            "Mozilla.Firefox  Mozilla.Firefox  120.0  winget\n"
            "Firefox.Dev  Firefox.Dev  120.0  winget\n"
        )
        self.assertEqual(WingetManager.parse_search(out), ["Mozilla.Firefox", "Firefox.Dev"])

    def test_brew(self):
        out = "==> Formulae\nhtop\n==> Casks\ntailscale\n"
        self.assertEqual(BrewManager.parse_search(out), ["htop", "tailscale"])


class TestServerUrls(unittest.TestCase):
    def test_pacman_reads_mirrorlist(self):
        data = "# mirror\nServer = https://fast.example/archlinux/$repo/os/$arch\n"
        with patch("builtins.open", unittest.mock.mock_open(read_data=data)):
            self.assertEqual(
                PacmanManager().server(), "https://fast.example/archlinux/$repo/os/$arch"
            )

    def test_flatpak_server(self):
        self.assertEqual(FlatpakManager().server(), "https://dl.flathub.org")

    def test_apt_falls_back(self):
        with patch("builtins.open", side_effect=OSError):
            self.assertEqual(AptManager().server(), "http://deb.debian.org/debian")


class TestPickFastest(unittest.TestCase):
    def test_picks_lowest_latency(self):
        with patch("enj.speed.measure", side_effect=[50.0, 20.0, None]):
            url, ms = pick_fastest(["a", "b", "c"])
            self.assertEqual((url, ms), ("b", 20.0))

    def test_all_unreachable_returns_none(self):
        with patch("enj.speed.measure", return_value=None):
            self.assertIsNone(pick_fastest(["a", "b"]))


if __name__ == "__main__":
    unittest.main()
