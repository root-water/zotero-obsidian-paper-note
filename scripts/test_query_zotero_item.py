#!/usr/bin/env python
"""Regression tests for query_zotero_item.py."""

from __future__ import annotations

import argparse
import sqlite3
import tempfile
import unittest
from pathlib import Path

import query_zotero_item


class QueryZoteroItemTest(unittest.TestCase):
    def test_returns_notes_annotations_and_fulltext_cache(self) -> None:
        with tempfile.TemporaryDirectory(prefix="codex-zotero-test-") as temp:
            root = Path(temp)
            db_path = root / "zotero.sqlite"
            pdf_dir = root / "storage" / "PDFKEY"
            pdf_dir.mkdir(parents=True)
            (pdf_dir / "paper.pdf").write_bytes(b"%PDF-1.4\n")
            (pdf_dir / ".zotero-ft-cache").write_text("full text cache body", encoding="utf-8")

            self._create_database(db_path)

            args = argparse.Namespace(
                db=str(db_path),
                title="Test Paper",
                doi="10.1234/example",
                collection="光",
                limit=10,
                copy_db=False,
            )
            result = query_zotero_item.run_query(args, copy_db=False)

            item = result["items"][0]
            self.assertEqual("ITEMKEY", item["key"])
            self.assertEqual("Child note title", item["notes"][0]["title"])
            self.assertIn("important child note", item["notes"][0]["note"])
            self.assertEqual("PDFKEY", item["annotations"][0]["attachmentKey"])
            self.assertEqual("annotation text", item["annotations"][0]["text"])
            self.assertEqual("full text cache body", item["attachments"][0]["fulltext"]["cacheText"])

    def _create_database(self, db_path: Path) -> None:
        conn = sqlite3.connect(db_path)
        conn.executescript(
            """
            create table fields (fieldID integer primary key, fieldName text);
            create table itemData (itemID int, fieldID int, valueID int);
            create table itemDataValues (valueID integer primary key, value text);
            create table itemTypes (itemTypeID integer primary key, typeName text);
            create table items (
                itemID integer primary key,
                itemTypeID int not null,
                dateAdded timestamp default current_timestamp,
                dateModified timestamp default current_timestamp,
                key text not null
            );
            create table deletedItems (itemID integer primary key);
            create table creatorTypes (creatorTypeID integer primary key, creatorType text);
            create table creators (creatorID integer primary key, firstName text, lastName text);
            create table itemCreators (itemID int, creatorID int, creatorTypeID int, orderIndex int);
            create table collections (collectionID integer primary key, collectionName text, key text);
            create table collectionItems (collectionID int, itemID int, orderIndex int default 0);
            create table itemAttachments (
                itemID integer primary key,
                parentItemID int,
                path text,
                contentType text
            );
            create table itemNotes (itemID integer primary key, parentItemID int, note text, title text);
            create table itemAnnotations (
                itemID integer primary key,
                parentItemID int not null,
                type integer not null,
                authorName text,
                text text,
                comment text,
                color text,
                pageLabel text,
                sortIndex text not null,
                position text not null,
                isExternal int not null
            );
            create table fulltextItems (
                itemID integer primary key,
                indexedPages int,
                totalPages int,
                indexedChars int,
                totalChars int,
                version int default 0,
                synced int default 0
            );
            """
        )
        conn.executemany(
            "insert into fields(fieldID, fieldName) values (?, ?)",
            [(1, "title"), (2, "DOI"), (3, "publicationTitle"), (4, "date")],
        )
        conn.executemany(
            "insert into itemTypes(itemTypeID, typeName) values (?, ?)",
            [(1, "journalArticle"), (2, "attachment"), (3, "note"), (4, "annotation")],
        )
        conn.executemany(
            "insert into items(itemID, itemTypeID, key) values (?, ?, ?)",
            [(10, 1, "ITEMKEY"), (20, 2, "PDFKEY"), (30, 3, "NOTEKEY"), (40, 4, "ANNOKEY")],
        )
        conn.executemany(
            "insert into itemDataValues(valueID, value) values (?, ?)",
            [(1, "Test Paper"), (2, "10.1234/example"), (3, "Journal"), (4, "2026")],
        )
        conn.executemany(
            "insert into itemData(itemID, fieldID, valueID) values (?, ?, ?)",
            [(10, 1, 1), (10, 2, 2), (10, 3, 3), (10, 4, 4), (20, 1, 1)],
        )
        conn.execute("insert into creatorTypes values (1, 'author')")
        conn.execute("insert into creators values (1, 'Ada', 'Lovelace')")
        conn.execute("insert into itemCreators values (10, 1, 1, 0)")
        conn.execute("insert into collections values (1, '光', 'COLKEY')")
        conn.execute("insert into collectionItems values (1, 10, 0)")
        conn.execute("insert into itemAttachments values (20, 10, 'storage:paper.pdf', 'application/pdf')")
        conn.execute("insert into itemNotes values (30, 10, '<p>important child note</p>', 'Child note title')")
        conn.execute(
            """
            insert into itemAnnotations
            values (40, 20, 1, 'Reviewer', 'annotation text', 'annotation comment',
                    '#ffd400', '3', '0001', '{"pageIndex":2}', 0)
            """
        )
        conn.execute("insert into fulltextItems values (20, 1, 1, 20, 20, 0, 0)")
        conn.commit()
        conn.close()


if __name__ == "__main__":
    unittest.main()
