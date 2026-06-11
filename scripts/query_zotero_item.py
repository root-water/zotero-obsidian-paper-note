#!/usr/bin/env python
"""Find Zotero items and PDF attachments from a local zotero.sqlite database.

The script is intentionally read-only. If Zotero locks the live database, it
automatically retries against a temporary copy.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Query Zotero paper metadata.")
    parser.add_argument("--db", required=True, help="Path to zotero.sqlite.")
    parser.add_argument("--title", default="", help="Title keyword or exact title.")
    parser.add_argument("--doi", default="", help="DOI to match.")
    parser.add_argument("--collection", default="", help="Collection name keyword.")
    parser.add_argument("--limit", type=int, default=10, help="Maximum candidates to return.")
    parser.add_argument("--copy-db", action="store_true", help="Copy database to temp before querying.")
    return parser.parse_args()


def connect_db(db_path: Path, copy_db: bool) -> tuple[sqlite3.Connection, tempfile.TemporaryDirectory[str] | None, Path]:
    temp_dir: tempfile.TemporaryDirectory[str] | None = None
    query_path = db_path
    if copy_db:
        temp_dir = tempfile.TemporaryDirectory(prefix="codex-zotero-query-")
        query_path = Path(temp_dir.name) / "zotero.sqlite"
        shutil.copy2(db_path, query_path)

    conn = sqlite3.connect(f"file:{query_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn, temp_dir, query_path


def get_field_map(conn: sqlite3.Connection) -> dict[int, str]:
    return {row["fieldID"]: row["fieldName"] for row in conn.execute("select fieldID, fieldName from fields")}


def get_item_fields(conn: sqlite3.Connection, item_id: int, field_names: dict[int, str]) -> dict[str, str]:
    rows = conn.execute(
        """
        select itemData.fieldID, itemDataValues.value
        from itemData
        join itemDataValues on itemData.valueID = itemDataValues.valueID
        where itemData.itemID = ?
        """,
        (item_id,),
    )
    fields: dict[str, str] = {}
    for row in rows:
        name = field_names.get(row["fieldID"], str(row["fieldID"]))
        fields[name] = row["value"]
    return fields


def get_creators(conn: sqlite3.Connection, item_id: int) -> list[dict[str, str]]:
    rows = conn.execute(
        """
        select creatorTypes.creatorType, creators.firstName, creators.lastName, itemCreators.orderIndex
        from itemCreators
        join creators on itemCreators.creatorID = creators.creatorID
        join creatorTypes on itemCreators.creatorTypeID = creatorTypes.creatorTypeID
        where itemCreators.itemID = ?
        order by itemCreators.orderIndex
        """,
        (item_id,),
    )
    return [
        {
            "type": row["creatorType"] or "",
            "firstName": row["firstName"] or "",
            "lastName": row["lastName"] or "",
            "name": " ".join(part for part in [row["firstName"], row["lastName"]] if part),
        }
        for row in rows
    ]


def get_collections(conn: sqlite3.Connection, item_id: int) -> list[dict[str, str]]:
    rows = conn.execute(
        """
        select collections.collectionName, collections.key
        from collectionItems
        join collections on collectionItems.collectionID = collections.collectionID
        where collectionItems.itemID = ?
        order by collections.collectionName
        """,
        (item_id,),
    )
    return [{"name": row["collectionName"], "key": row["key"]} for row in rows]


def table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "select 1 from sqlite_master where type = 'table' and name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def resolve_attachment_path(zotero_dir: Path, attachment_key: str, path_value: str) -> str:
    if path_value.startswith("storage:"):
        filename = path_value.split(":", 1)[1]
        return str(zotero_dir / "storage" / attachment_key / filename)
    return path_value


def html_to_text(value: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", value, flags=re.IGNORECASE)
    text = re.sub(r"</p\s*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def get_fulltext(conn: sqlite3.Connection, attachment_id: int, resolved_path: str) -> dict[str, Any]:
    fulltext: dict[str, Any] = {
        "indexedPages": None,
        "totalPages": None,
        "indexedChars": None,
        "totalChars": None,
        "cachePath": "",
        "cacheExists": False,
        "cacheText": "",
    }
    if table_exists(conn, "fulltextItems"):
        row = conn.execute(
            """
            select indexedPages, totalPages, indexedChars, totalChars
            from fulltextItems
            where itemID = ?
            """,
            (attachment_id,),
        ).fetchone()
        if row:
            fulltext.update(
                {
                    "indexedPages": row["indexedPages"],
                    "totalPages": row["totalPages"],
                    "indexedChars": row["indexedChars"],
                    "totalChars": row["totalChars"],
                }
            )

    if resolved_path:
        cache_path = Path(resolved_path).parent / ".zotero-ft-cache"
        fulltext["cachePath"] = str(cache_path)
        fulltext["cacheExists"] = cache_path.exists()
        if cache_path.exists():
            fulltext["cacheText"] = cache_path.read_text(encoding="utf-8", errors="replace")
    return fulltext


def get_notes(conn: sqlite3.Connection, parent_id: int) -> list[dict[str, Any]]:
    if not table_exists(conn, "itemNotes"):
        return []
    rows = conn.execute(
        """
        select itemNotes.itemID, items.key, itemNotes.title, itemNotes.note
        from itemNotes
        join items on itemNotes.itemID = items.itemID
        where itemNotes.parentItemID = ?
        order by items.dateAdded
        """,
        (parent_id,),
    )
    return [
        {
            "itemID": row["itemID"],
            "key": row["key"],
            "title": row["title"] or "",
            "note": html_to_text(row["note"] or ""),
            "html": row["note"] or "",
        }
        for row in rows
    ]


def get_annotations(conn: sqlite3.Connection, attachment_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not table_exists(conn, "itemAnnotations") or not attachment_rows:
        return []
    attachment_by_id = {attachment["itemID"]: attachment for attachment in attachment_rows}
    placeholders = ",".join("?" for _ in attachment_by_id)
    rows = conn.execute(
        f"""
        select itemAnnotations.itemID, items.key, itemAnnotations.parentItemID,
               itemAnnotations.type, itemAnnotations.authorName, itemAnnotations.text,
               itemAnnotations.comment, itemAnnotations.color, itemAnnotations.pageLabel,
               itemAnnotations.sortIndex, itemAnnotations.position, itemAnnotations.isExternal
        from itemAnnotations
        join items on itemAnnotations.itemID = items.itemID
        where itemAnnotations.parentItemID in ({placeholders})
        order by itemAnnotations.parentItemID, itemAnnotations.sortIndex
        """,
        tuple(attachment_by_id),
    )
    annotations = []
    for row in rows:
        attachment = attachment_by_id[row["parentItemID"]]
        annotations.append(
            {
                "itemID": row["itemID"],
                "key": row["key"],
                "attachmentItemID": row["parentItemID"],
                "attachmentKey": attachment["key"],
                "type": row["type"],
                "authorName": row["authorName"] or "",
                "text": row["text"] or "",
                "comment": row["comment"] or "",
                "color": row["color"] or "",
                "pageLabel": row["pageLabel"] or "",
                "sortIndex": row["sortIndex"] or "",
                "position": row["position"] or "",
                "isExternal": bool(row["isExternal"]),
            }
        )
    return annotations


def get_attachments(
    conn: sqlite3.Connection,
    parent_id: int,
    zotero_dir: Path,
    field_names: dict[int, str],
) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        select child.itemID, child.key, itemAttachments.path, itemAttachments.contentType
        from itemAttachments
        join items child on itemAttachments.itemID = child.itemID
        where itemAttachments.parentItemID = ?
        order by child.dateAdded
        """,
        (parent_id,),
    )
    attachments = []
    for row in rows:
        path_value = row["path"] or ""
        resolved = resolve_attachment_path(zotero_dir, row["key"], path_value) if path_value else ""
        fields = get_item_fields(conn, row["itemID"], field_names)
        attachments.append(
            {
                "itemID": row["itemID"],
                "key": row["key"],
                "title": fields.get("title", ""),
                "contentType": row["contentType"] or "",
                "path": path_value,
                "resolvedPath": resolved,
                "exists": Path(resolved).exists() if resolved else False,
                "fulltext": get_fulltext(conn, row["itemID"], resolved),
            }
        )
    return attachments


def item_type(conn: sqlite3.Connection, item_id: int) -> str:
    row = conn.execute(
        """
        select itemTypes.typeName
        from items
        join itemTypes on items.itemTypeID = itemTypes.itemTypeID
        where items.itemID = ?
        """,
        (item_id,),
    ).fetchone()
    return row["typeName"] if row else ""


def candidate_item_ids(conn: sqlite3.Connection, title: str, doi: str, limit: int) -> list[int]:
    conditions = ["items.itemID not in (select itemID from deletedItems)"]
    params: list[str] = []
    if title:
        conditions.append(
            """
            exists (
              select 1 from itemData d
              join fields f on d.fieldID = f.fieldID
              join itemDataValues v on d.valueID = v.valueID
              where d.itemID = items.itemID and f.fieldName = 'title' and lower(v.value) like ?
            )
            """
        )
        params.append(f"%{title.lower()}%")
    if doi:
        conditions.append(
            """
            exists (
              select 1 from itemData d
              join fields f on d.fieldID = f.fieldID
              join itemDataValues v on d.valueID = v.valueID
              where d.itemID = items.itemID and f.fieldName = 'DOI' and lower(v.value) = ?
            )
            """
        )
        params.append(doi.lower())

    sql = f"""
        select items.itemID
        from items
        join itemTypes on items.itemTypeID = itemTypes.itemTypeID
        where {' and '.join(conditions)}
          and itemTypes.typeName not in ('attachment', 'note', 'annotation')
        order by items.dateModified desc
        limit ?
    """
    params.append(str(limit))
    return [row["itemID"] for row in conn.execute(sql, params)]


def score_match(item: dict[str, Any], title: str, doi: str, collection: str) -> int:
    score = 0
    fields = item["fields"]
    if doi and fields.get("DOI", "").lower() == doi.lower():
        score += 100
    if title and title.lower() in fields.get("title", "").lower():
        score += 50
    if collection:
        collection_lc = collection.lower()
        if any(collection_lc in c["name"].lower() for c in item["collections"]):
            score += 30
    if any(att["contentType"] == "application/pdf" or att["resolvedPath"].lower().endswith(".pdf") for att in item["attachments"]):
        score += 10
    return score


def run_query(args: argparse.Namespace, copy_db: bool) -> dict[str, Any]:
    db_path = Path(args.db)
    zotero_dir = db_path.parent
    conn, temp_dir, query_path = connect_db(db_path, copy_db)

    try:
        field_names = get_field_map(conn)
        item_ids = candidate_item_ids(conn, args.title.strip(), args.doi.strip(), args.limit * 3)
        items = []
        for item_id in item_ids:
            fields = get_item_fields(conn, item_id, field_names)
            collections = get_collections(conn, item_id)
            if args.collection and not any(args.collection.lower() in c["name"].lower() for c in collections):
                continue
            key_row = conn.execute("select key from items where itemID = ?", (item_id,)).fetchone()
            item = {
                "itemID": item_id,
                "key": key_row["key"] if key_row else "",
                "type": item_type(conn, item_id),
                "fields": fields,
                "creators": get_creators(conn, item_id),
                "collections": collections,
                "attachments": get_attachments(conn, item_id, zotero_dir, field_names),
                "notes": get_notes(conn, item_id),
            }
            item["annotations"] = get_annotations(conn, item["attachments"])
            item["score"] = score_match(item, args.title.strip(), args.doi.strip(), args.collection.strip())
            items.append(item)

        items.sort(key=lambda item: item["score"], reverse=True)
        return {
            "database": str(db_path),
            "queryDatabase": str(query_path),
            "copiedDatabase": copy_db,
            "query": {"title": args.title, "doi": args.doi, "collection": args.collection},
            "count": len(items[: args.limit]),
            "items": items[: args.limit],
        }
    finally:
        conn.close()
        if temp_dir is not None:
            temp_dir.cleanup()


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args()

    try:
        result = run_query(args, args.copy_db)
    except sqlite3.OperationalError as exc:
        if args.copy_db or "locked" not in str(exc).lower():
            raise
        result = run_query(args, True)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
