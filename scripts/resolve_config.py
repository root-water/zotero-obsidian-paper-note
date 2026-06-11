#!/usr/bin/env python
"""Resolve portable Zotero/Obsidian paths for this skill."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


ENV_MAP = {
    "obsidianVaultRoot": "ZOTERO_OBSIDIAN_VAULT",
    "paperNotesRoot": "ZOTERO_OBSIDIAN_PAPER_ROOT",
    "zoteroDataDir": "ZOTERO_DATA_DIR",
    "zoteroDatabase": "ZOTERO_DB",
}


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise SystemExit(f"Config must be a JSON object: {path}")
    return data


def common_zotero_data_dir() -> Path | None:
    candidates: list[Path] = []
    home = Path.home()
    if os.name == "nt":
        candidates.extend(
            [
                home / "Zotero",
                home / "Documents" / "Zotero",
                Path(os.environ.get("USERPROFILE", str(home))) / "Zotero",
            ]
        )
    elif sys.platform == "darwin":
        candidates.append(home / "Zotero")
    else:
        candidates.extend([home / "Zotero", home / ".zotero" / "zotero"])
    for candidate in candidates:
        if (candidate / "zotero.sqlite").exists():
            return candidate
    return None


def normalize_path(value: str) -> str:
    if not value:
        return ""
    return str(Path(value).expanduser())


def resolve() -> dict[str, str]:
    template = read_json(ROOT / "skill-config.json")
    local = read_json(ROOT / "skill-config.local.json")
    config: dict[str, str] = {}
    for key in ENV_MAP:
        value = os.environ.get(ENV_MAP[key]) or local.get(key) or template.get(key) or ""
        config[key] = normalize_path(str(value))

    if not config["zoteroDataDir"]:
        detected = common_zotero_data_dir()
        if detected:
            config["zoteroDataDir"] = str(detected)
    if not config["zoteroDatabase"] and config["zoteroDataDir"]:
        config["zoteroDatabase"] = str(Path(config["zoteroDataDir"]) / "zotero.sqlite")
    if not config["paperNotesRoot"] and config["obsidianVaultRoot"]:
        config["paperNotesRoot"] = str(Path(config["obsidianVaultRoot"]) / "论文")
    return config


def status(config: dict[str, str]) -> dict[str, Any]:
    checks: dict[str, Any] = {}
    for key, value in config.items():
        checks[key] = {"path": value, "exists": bool(value) and Path(value).exists()}
    zotero_db = config.get("zoteroDatabase", "")
    checks["zoteroDatabase"]["looksValid"] = bool(zotero_db) and Path(zotero_db).name == "zotero.sqlite"
    storage = Path(config.get("zoteroDataDir", "")) / "storage" if config.get("zoteroDataDir") else Path()
    checks["zoteroStorage"] = {"path": str(storage) if config.get("zoteroDataDir") else "", "exists": storage.exists()}
    return checks


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Resolve Zotero/Obsidian skill configuration.")
    parser.add_argument("--json", action="store_true", help="Print resolved config as JSON.")
    parser.add_argument("--show", action="store_true", help="Print resolved config and path checks.")
    args = parser.parse_args()

    config = resolve()
    if args.json:
        print(json.dumps(config, ensure_ascii=False, indent=2))
        return
    if args.show or True:
        print(json.dumps({"config": config, "checks": status(config)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
