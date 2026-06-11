# Zotero and Figure Tooling

Read this when Zotero CLI is unavailable, metadata/PDF lookup is needed, or figure crops are requested.

## Portable Path Configuration

On a new computer, first try automatic discovery:

```powershell
python scripts\resolve_config.py --show
```

The resolver searches common user folders, Documents/OneDrive/Dropbox/iCloud locations, and relevant workspace ancestors. It identifies Zotero by `zotero.sqlite` plus `storage`, and Obsidian vaults by `.obsidian`, preferring vaults that already contain `论文`.

If discovery is ambiguous, inspect candidates:

```powershell
python scripts\resolve_config.py --discover
```

Use environment variables or `skill-config.local.json` only to override or disambiguate paths.

Environment variables:

| Purpose | Variable |
| --- | --- |
| Obsidian vault root | `ZOTERO_OBSIDIAN_VAULT` |
| Paper notes root | `ZOTERO_OBSIDIAN_PAPER_ROOT` |
| Zotero data directory | `ZOTERO_DATA_DIR` |
| Zotero database | `ZOTERO_DB` |
| Limit discovery roots | `ZOTERO_OBSIDIAN_SEARCH_ROOTS` |

`ZOTERO_OBSIDIAN_SEARCH_ROOTS` uses the platform path separator (`;` on Windows, `:` on macOS/Linux).

Inspect resolved paths at any time:

```powershell
python scripts\resolve_config.py --show
```

Minimal `skill-config.local.json`:

```json
{
  "obsidianVaultRoot": "D:/path/to/Obsidian/Issue",
  "paperNotesRoot": "D:/path/to/Obsidian/Issue/论文",
  "zoteroDataDir": "D:/path/to/Zotero",
  "zoteroDatabase": "D:/path/to/Zotero/zotero.sqlite"
}
```

After migration, run:

```powershell
python scripts\smoke_test.py --title "known paper title"
```

## Zotero Query Helper

Prefer the bundled helper before manual SQLite work:

```powershell
$env:PYTHONIOENCODING = 'utf-8'
$cfg = python scripts\resolve_config.py --json | ConvertFrom-Json
python scripts\query_zotero_item.py --db $cfg.zoteroDatabase --title "paper title" --collection "光"
python scripts\query_zotero_item.py --db $cfg.zoteroDatabase --doi "10.1038/s41928-020-00466-9"
```

The JSON includes metadata, creators, collections, Zotero keys, PDF attachment paths, child notes, PDF annotations, full-text cache hints, and `copiedDatabase`. If the live Zotero database is locked, the helper retries against a temporary copy.

Useful output fields:

| Field | Use |
| --- | --- |
| `items[].fields` | Title, DOI, journal, date, abstract, and other Zotero metadata. |
| `items[].creators` | Authors/editors in Zotero order. |
| `items[].collections` | Folder/category mirroring under `论文`. |
| `items[].attachments[]` | PDF key/path/existence and full-text cache details. |
| `items[].attachments[].fulltext.cacheText` | Zotero indexed text when available; still read the PDF for figures and context. |
| `items[].notes[]` | Zotero child notes, stripped to readable text with original HTML retained. |
| `items[].annotations[]` | PDF highlights/comments with attachment key, page label, color, text, comment, and position. |

If multiple candidates are returned, choose the one that best matches DOI/title/collection. Report ambiguity only when the choice is genuinely unclear.

## Manual SQLite Fallback

Use Python `sqlite3` read-only, ideally against a copied database:

```python
import sqlite3
conn = sqlite3.connect("file:path/to/zotero.sqlite?mode=ro", uri=True)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
```

Useful tables:

| Need | Tables |
| --- | --- |
| Item title and fields | `items`, `itemTypes`, `itemData`, `itemDataValues`, `fields` |
| Creators | `itemCreators`, `creators`, `creatorTypes` |
| Collections | `collections`, `collectionItems` |
| Attachments | `itemAttachments`, `items` |
| Child notes | `itemNotes`, `items` |

Set `PYTHONIOENCODING=utf-8` before printing JSON in PowerShell if Chinese text appears garbled.

## Figure Cropping

Use the helper by absolute path or resolve it relative to this skill directory.

First render preview pages or a contact sheet to locate figures and figure captions:

```powershell
python scripts\render_pdf_crops.py --pdf "paper.pdf" --out-dir "vault\论文\_assets\<category>\paper-slug\preview" --preview-pages "1-6" --contact-sheet "contact-sheet.png" --preview-scale 1.6
```

Preview files are named `page-001.png`, `page-002.png`, etc. Measure crop boxes on those preview images and set each crop's `source_scale` to the preview scale used.

For journal figures, use the caption-boundary rule: crop the visual region above the `Fig. N | ...` / `Figure N.` caption start. Include full axes, units, legends, colorbars, and multi-row panels. Add small bottom padding instead of clipping tightly.

Then render final crops:

```powershell
python scripts\render_pdf_crops.py --pdf "paper.pdf" --out-dir "vault\论文\_assets\<category>\paper-slug" --crops crops.json --scale 3.2
```

`render_pdf_crops.py` tries `pypdfium2` first and falls back to PyMuPDF (`fitz`). If both are missing, install one:

```powershell
$target = Join-Path $env:TEMP 'codex-pypdfium2-render'
python -m pip install --quiet --target $target pypdfium2
$env:PYTHONPATH = $target
# or:
python -m pip install PyMuPDF Pillow
```

Crop config:

```json
[
  {"page": 3, "name": "fig1-lgmd-device-architecture.png", "box": [60, 90, 900, 585], "source_scale": 1.6}
]
```

`box` is `[left, top, right, bottom]` measured on a preview rendered at `source_scale`.

Remove preview pages/contact sheets after final crops are embedded unless the user asks to keep them.
