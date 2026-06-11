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

SKIP_DIR_NAMES = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    "env",
    "AppData",
    "Application Data",
    "Library",
    "Windows",
    "Program Files",
    "Program Files (x86)",
}

DISCOVERY_LIMIT = 25000
DISCOVERY_DEPTH = 5


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise SystemExit(f"Config must be a JSON object: {path}")
    return data


def dedupe_paths(paths: list[Path]) -> list[Path]:
    seen: set[str] = set()
    result: list[Path] = []
    for path in paths:
        try:
            key = str(path.expanduser().resolve()).lower()
        except OSError:
            key = str(path.expanduser()).lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(path.expanduser())
    return result


def path_depth_from(path: Path, root: Path) -> int:
    try:
        return len(path.resolve().relative_to(root.resolve()).parts)
    except (OSError, ValueError):
        return 999


def configured_search_roots() -> list[Path]:
    raw = os.environ.get("ZOTERO_OBSIDIAN_SEARCH_ROOTS", "")
    if raw:
        return dedupe_paths([Path(part) for part in raw.split(os.pathsep) if part.strip()])

    home = Path.home()
    roots: list[Path] = [
        home,
        home / "Documents",
        home / "Desktop",
        home / "OneDrive",
        home / "Dropbox",
        home / "iCloudDrive",
    ]

    user_profile = os.environ.get("USERPROFILE")
    if user_profile:
        profile = Path(user_profile)
        roots.extend([profile, profile / "Documents", profile / "Desktop", profile / "OneDrive"])

    for key, value in os.environ.items():
        if "ONEDRIVE" in key.upper() and value:
            roots.extend([Path(value), Path(value) / "Documents"])

    for parent in [Path.cwd(), *Path.cwd().parents, ROOT, *ROOT.parents]:
        if parent.name.lower() in {"documents", "desktop"}:
            roots.append(parent)
        if parent.name.lower() in {"obsidian", "zotero"}:
            roots.append(parent.parent)

    return dedupe_paths([path for path in roots if path.exists() and path.is_dir()])


def iter_dirs(root: Path, max_depth: int = DISCOVERY_DEPTH, limit: int = DISCOVERY_LIMIT):
    stack = [root]
    visited = 0
    root = root.expanduser()
    while stack and visited < limit:
        current = stack.pop()
        visited += 1
        yield current
        if path_depth_from(current, root) >= max_depth:
            continue
        try:
            children = [child for child in current.iterdir() if child.is_dir()]
        except (OSError, PermissionError):
            continue
        for child in reversed(children):
            if child.name in SKIP_DIR_NAMES or child.name.startswith(".Trash"):
                continue
            stack.append(child)


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


def zotero_candidates() -> list[dict[str, Any]]:
    candidates: dict[str, dict[str, Any]] = {}
    if not os.environ.get("ZOTERO_OBSIDIAN_SEARCH_ROOTS"):
        common = common_zotero_data_dir()
        if common:
            candidates[str(common.resolve()).lower()] = score_zotero_dir(common)

    for root in configured_search_roots():
        for directory in iter_dirs(root):
            db = directory / "zotero.sqlite"
            if not db.exists():
                continue
            try:
                key = str(directory.resolve()).lower()
            except OSError:
                key = str(directory).lower()
            candidates[key] = score_zotero_dir(directory)

    return sorted(candidates.values(), key=lambda item: item["score"], reverse=True)


def score_zotero_dir(path: Path) -> dict[str, Any]:
    storage = path / "storage"
    db = path / "zotero.sqlite"
    score = 0
    if db.exists():
        score += 100
    if storage.exists():
        score += 40
    if path.name.lower() == "zotero":
        score += 20
    if path.parent.name.lower() in {"documents", "desktop"}:
        score += 5
    try:
        modified = db.stat().st_mtime if db.exists() else 0
    except OSError:
        modified = 0
    return {
        "path": str(path),
        "database": str(db),
        "storage": str(storage),
        "databaseExists": db.exists(),
        "storageExists": storage.exists(),
        "score": score,
        "modified": modified,
    }


def obsidian_candidates() -> list[dict[str, Any]]:
    candidates: dict[str, dict[str, Any]] = {}
    for root in configured_search_roots():
        for directory in iter_dirs(root):
            if not (directory / ".obsidian").exists():
                continue
            try:
                key = str(directory.resolve()).lower()
            except OSError:
                key = str(directory).lower()
            candidates[key] = score_obsidian_vault(directory)
    return sorted(candidates.values(), key=lambda item: item["score"], reverse=True)


def score_obsidian_vault(path: Path) -> dict[str, Any]:
    paper_root = path / "论文"
    md_count = 0
    try:
        md_count = sum(1 for child in path.glob("*.md") if child.is_file())
    except OSError:
        md_count = 0
    score = 0
    if (path / ".obsidian").exists():
        score += 100
    if paper_root.exists():
        score += 50
    if md_count:
        score += min(md_count, 20)
    if path.name.lower() in {"obsidian", "vault", "issue", "notes"}:
        score += 5
    return {
        "path": str(path),
        "paperNotesRoot": str(paper_root),
        "hasObsidianConfig": (path / ".obsidian").exists(),
        "paperNotesRootExists": paper_root.exists(),
        "topLevelMarkdownCount": md_count,
        "score": score,
    }


def pick_unambiguous(candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]
    if candidates[0]["score"] > candidates[1]["score"]:
        return candidates[0]
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
        detected = pick_unambiguous(zotero_candidates())
        if detected:
            config["zoteroDataDir"] = detected["path"]
    if not config["zoteroDatabase"] and config["zoteroDataDir"]:
        config["zoteroDatabase"] = str(Path(config["zoteroDataDir"]) / "zotero.sqlite")
    if not config["obsidianVaultRoot"]:
        detected_vault = pick_unambiguous(obsidian_candidates())
        if detected_vault:
            config["obsidianVaultRoot"] = detected_vault["path"]
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
    checks["obsidianVaultRoot"]["looksValid"] = bool(config.get("obsidianVaultRoot")) and (Path(config["obsidianVaultRoot"]) / ".obsidian").exists()
    return checks


def discovery_report() -> dict[str, Any]:
    roots = [str(path) for path in configured_search_roots()]
    zotero = zotero_candidates()
    obsidian = obsidian_candidates()
    return {
        "searchRoots": roots,
        "zoteroCandidates": zotero[:10],
        "obsidianCandidates": obsidian[:10],
        "zoteroAmbiguous": bool(zotero) and pick_unambiguous(zotero) is None,
        "obsidianAmbiguous": bool(obsidian) and pick_unambiguous(obsidian) is None,
    }


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Resolve Zotero/Obsidian skill configuration.")
    parser.add_argument("--json", action="store_true", help="Print resolved config as JSON.")
    parser.add_argument("--show", action="store_true", help="Print resolved config and path checks.")
    parser.add_argument("--discover", action="store_true", help="Print auto-discovery candidates.")
    args = parser.parse_args()

    config = resolve()
    if args.json:
        print(json.dumps(config, ensure_ascii=False, indent=2))
        return
    if args.discover:
        print(json.dumps(discovery_report(), ensure_ascii=False, indent=2))
        return
    if args.show or True:
        print(json.dumps({"config": config, "checks": status(config), "discovery": discovery_report()}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
