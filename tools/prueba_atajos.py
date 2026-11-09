#!/usr/bin/env python3
"""Regression tests for reading the active Niri KDL keybinding tree."""

import os
import tempfile
import unittest
from pathlib import Path

import atajos


class ShortcutReaderTests(unittest.TestCase):
    def test_reads_multiline_bindings_and_recursive_includes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.kdl"
            fragments = root / "config.d"
            fragments.mkdir()
            (fragments / "extra.kdl").write_text(
                'binds {\n'
                '    // ----- Media -----\n'
                '    XF86AudioPlay {\n'
                '        spawn "quickshell" "ipc" "call" "k4" "togglePlay"\n'
                '    }\n'
                '}\n',
                encoding="utf-8",
            )
            config.write_text(
                'include "config.d/*.kdl"\n'
                'binds {\n'
                '    // ----- General -----\n'
                '    Mod+Return { spawn "quickshell" "ipc" "call" "k4.term" "abrir"; }\n'
                '    Mod+X { spawn-sh "printf \\\"{\\\"\\n"; }\n'
                '}\n',
                encoding="utf-8",
            )

            original = atajos.NIRI_CONFIG
            try:
                atajos.NIRI_CONFIG = str(config)
                bindings = atajos.read_bindings()
            finally:
                atajos.NIRI_CONFIG = original

            by_combo = {item["combo"]: item for item in bindings}
            self.assertEqual(set(by_combo), {"Mod+Return", "Mod+X", "XF86AudioPlay"})
            self.assertEqual(by_combo["Mod+Return"]["hace"], "K4 · k4.term · abrir")
            self.assertEqual(by_combo["Mod+Return"]["seccion"], "General")
            self.assertEqual(by_combo["XF86AudioPlay"]["seccion"], "Media")
            self.assertIn("{", by_combo["Mod+X"]["hace"])


if __name__ == "__main__":
    unittest.main()
