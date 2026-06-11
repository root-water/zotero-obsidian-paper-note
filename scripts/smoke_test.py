#!/usr/bin/env python
"""Smoke-test a migrated Zotero to Obsidian paper-note skill."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

import resolve_config


ROOT = Path(__file__).resolve().parents[1]


def module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def check_sqlite(db_path: Path) -> dict[str, object]:
    result: dict[str, object] = {"exists": db_path.exists(), "itemCount": None, "error": ""}
    if not db_path.exists():
        return result
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        try:
            row = conn.execute("select count(*) from items").fetchone()
            result["itemCount"] = int(row[0]) if row else None
        finally:
            conn.close()
    except Exception as exc:  # pragma: no cover - diagnostic surface
        if "locked" not in str(exc).lower():
            result["error"] = str(exc)
            return result
        try:
            with tempfile.TemporaryDirectory(prefix="zotero-skill-smoke-") as temp_dir:
                snapshot = Path(temp_dir) / "zotero.sqlite"
                shutil.copy2(db_path, snapshot)
                conn = sqlite3.connect(f"file:{snapshot}?mode=ro", uri=True)
                try:
                    row = conn.execute("select count(*) from items").fetchone()
                    result["itemCount"] = int(row[0]) if row else None
                    result["usedSnapshot"] = True
                finally:
                    conn.close()
        except Exception as copy_exc:  # pragma: no cover - diagnostic surface
            result["error"] = str(copy_exc)
    return result


def query_item(db_path: Path, title: str, doi: str) -> dict[str, object]:
    if not title and not doi:
        return {"skipped": True, "reason": "No --title or --doi provided."}
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "query_zotero_item.py"),
        "--db",
        str(db_path),
        "--limit",
        "3",
    ]
    if title:
        cmd.extend(["--title", title])
    if doi:
        cmd.extend(["--doi", doi])
    proc = subprocess.run(cmd, text=True, capture_output=True, encoding="utf-8", errors="replace", check=False)
    if proc.returncode != 0:
        return {"ok": False, "returncode": proc.returncode, "stderr": proc.stderr.strip()}
    data = json.loads(proc.stdout)
    pdfs = []
    for item in data.get("items", []):
        for attachment in item.get("attachments", []):
            if attachment.get("contentType") == "application/pdf" or str(attachment.get("resolvedPath", "")).lower().endswith(".pdf"):
                pdfs.append(
                    {
                        "itemKey": item.get("key", ""),
                        "pdfKey": attachment.get("key", ""),
                        "resolvedPath": attachment.get("resolvedPath", ""),
                        "exists": attachment.get("exists", False),
                    }
                )
    return {"ok": True, "count": data.get("count", 0), "pdfs": pdfs}


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Smoke-test this portable skill.")
    parser.add_argument("--title", default="", help="Known Zotero title or title keyword to query.")
    parser.add_argument("--doi", default="", help="Known DOI to query.")
    args = parser.parse_args()

    config = resolve_config.resolve()
    zotero_db = Path(config.get("zoteroDatabase", ""))
    report = {
        "config": config,
        "paths": resolve_config.status(config),
        "python": sys.version,
        "dependencies": {
            "PIL": module_available("PIL"),
            "fitz": module_available("fitz"),
            "pypdfium2": module_available("pypdfium2"),
        },
        "zoteroDatabase": check_sqlite(zotero_db),
        "query": query_item(zotero_db, args.title, args.doi) if zotero_db else {"ok": False, "error": "No zoteroDatabase resolved."},
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))

    hard_fail = not zotero_db.exists() or bool(report["zoteroDatabase"].get("error"))
    if args.title or args.doi:
        hard_fail = hard_fail or not bool(report["query"].get("ok"))
    if hard_fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
