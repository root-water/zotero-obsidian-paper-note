# Zotero Obsidian Paper Note Skill

A portable Codex skill for turning local Zotero papers into Chinese Obsidian literature notes. It reads Zotero metadata, local PDFs, Zotero child notes, and PDF annotations, then creates or updates notes under an Obsidian `论文` folder with verified metadata, Zotero links, key figure crops, reading points, limitations, citation-ready ideas, and follow-up directions.

## What It Does

- Finds Zotero items by title, DOI, or collection.
- Resolves local Zotero PDF attachments and indexed full-text cache.
- Mirrors Zotero collections into Obsidian paper-note folders.
- Updates existing notes by Zotero item key, DOI, or title instead of duplicating them.
- Crops important figures with a caption-boundary workflow that preserves axes, units, legends, colorbars, and panel labels.
- Keeps machine-specific paths outside the published skill through environment variables or `skill-config.local.json`.

## Install

Copy this folder into your Codex skills directory:

```powershell
Copy-Item -Recurse . "$env:CODEX_HOME\skills\zotero-obsidian-paper-note"
```

Or unzip the release package so the final path looks like:

```text
%CODEX_HOME%\skills\zotero-obsidian-paper-note\SKILL.md
```

Restart Codex after installation if the skill list does not refresh automatically.

## Configure

Set environment variables:

```powershell
$env:ZOTERO_OBSIDIAN_VAULT = "D:\path\to\ObsidianVault"
$env:ZOTERO_OBSIDIAN_PAPER_ROOT = "D:\path\to\ObsidianVault\论文"
$env:ZOTERO_DATA_DIR = "D:\path\to\Zotero"
$env:ZOTERO_DB = "D:\path\to\Zotero\zotero.sqlite"
```

Or create `skill-config.local.json` next to `SKILL.md`:

```json
{
  "obsidianVaultRoot": "D:/path/to/ObsidianVault",
  "paperNotesRoot": "D:/path/to/ObsidianVault/论文",
  "zoteroDataDir": "D:/path/to/Zotero",
  "zoteroDatabase": "D:/path/to/Zotero/zotero.sqlite"
}
```

Do not commit `skill-config.local.json`; it is intentionally ignored.

## Check A New Machine

```powershell
python scripts\resolve_config.py --show
python scripts\smoke_test.py --title "known Zotero paper title"
python -m unittest discover -s scripts -p "test_*.py"
```

For figure rendering, install at least one PDF renderer:

```powershell
python -m pip install PyMuPDF Pillow
# optional alternative renderer
python -m pip install pypdfium2
```

## Usage Prompt Examples

```text
使用 zotero-obsidian-paper-note，把 Zotero 中 DOI 为 10.xxxx/yyyy 的论文整理成 Obsidian 中文精读笔记。
```

```text
阅读 Zotero 的 光 collection 中最近加入且有 PDF 的论文，写入 Obsidian 的 论文\光，关键图要裁剪进来。
```

## Repository Hygiene

This repository should contain only the reusable skill code, references, tests, and public examples. It should not contain Zotero databases, PDFs, Obsidian vault content, generated figure crops, local path configs, or temporary render outputs.

