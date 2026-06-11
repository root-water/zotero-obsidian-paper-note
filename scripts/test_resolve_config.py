#!/usr/bin/env python
"""Regression tests for resolve_config.py."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import resolve_config


CONFIG_ENV_KEYS = [
    "ZOTERO_OBSIDIAN_VAULT",
    "ZOTERO_OBSIDIAN_PAPER_ROOT",
    "ZOTERO_DATA_DIR",
    "ZOTERO_DB",
    "ZOTERO_OBSIDIAN_SEARCH_ROOTS",
]


class ResolveConfigTest(unittest.TestCase):
    def test_auto_discovers_zotero_and_obsidian_under_search_roots(self) -> None:
        with tempfile.TemporaryDirectory(prefix="zotero-skill-resolve-") as temp:
            root = Path(temp)
            zotero = root / "Documents" / "Zotero"
            zotero.mkdir(parents=True)
            (zotero / "zotero.sqlite").write_bytes(b"")
            (zotero / "storage").mkdir()

            vault = root / "Documents" / "Obsidian" / "Issue"
            (vault / ".obsidian").mkdir(parents=True)
            (vault / "论文").mkdir()

            with patch.dict(os.environ, {"ZOTERO_OBSIDIAN_SEARCH_ROOTS": str(root)}, clear=False):
                for key in CONFIG_ENV_KEYS[:-1]:
                    os.environ.pop(key, None)
                config = resolve_config.resolve()

            self.assertEqual(str(zotero), config["zoteroDataDir"])
            self.assertEqual(str(zotero / "zotero.sqlite"), config["zoteroDatabase"])
            self.assertEqual(str(vault), config["obsidianVaultRoot"])
            self.assertEqual(str(vault / "论文"), config["paperNotesRoot"])

    def test_environment_values_override_auto_discovery(self) -> None:
        with tempfile.TemporaryDirectory(prefix="zotero-skill-resolve-") as temp:
            root = Path(temp)
            discovered = root / "Documents" / "Zotero"
            discovered.mkdir(parents=True)
            (discovered / "zotero.sqlite").write_bytes(b"")

            explicit_zotero = root / "ExplicitZotero"
            explicit_vault = root / "ExplicitVault"
            env = {
                "ZOTERO_OBSIDIAN_SEARCH_ROOTS": str(root),
                "ZOTERO_DATA_DIR": str(explicit_zotero),
                "ZOTERO_DB": str(explicit_zotero / "zotero.sqlite"),
                "ZOTERO_OBSIDIAN_VAULT": str(explicit_vault),
                "ZOTERO_OBSIDIAN_PAPER_ROOT": str(explicit_vault / "Papers"),
            }
            with patch.dict(os.environ, env, clear=False):
                config = resolve_config.resolve()

            self.assertEqual(str(explicit_zotero), config["zoteroDataDir"])
            self.assertEqual(str(explicit_zotero / "zotero.sqlite"), config["zoteroDatabase"])
            self.assertEqual(str(explicit_vault), config["obsidianVaultRoot"])
            self.assertEqual(str(explicit_vault / "Papers"), config["paperNotesRoot"])

    def test_equal_score_obsidian_candidates_are_reported_as_ambiguous(self) -> None:
        candidates = [{"score": 100, "path": "one"}, {"score": 100, "path": "two"}]
        self.assertIsNone(resolve_config.pick_unambiguous(candidates))


if __name__ == "__main__":
    unittest.main()
