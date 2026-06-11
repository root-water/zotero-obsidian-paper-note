---
name: zotero-obsidian-paper-note
description: Use when the user asks to read, summarize, annotate, or organize Zotero papers into Obsidian literature notes, especially Chinese notes under 论文 folders, Zotero collections/categories, DOI/title lookups, local PDFs, figure crops, highlights, or existing-note updates across different computers.
---

# Zotero to Obsidian Paper Note

Turn a Zotero paper into a polished Obsidian literature note in the user's preferred long-form style: verified metadata, key figures near the top with reading points, PDF-grounded Chinese explanation, Zotero links, reading insights, citation-ready points, extension directions, and controlled `==highlights==`.

## Use For

- Reading a Zotero paper/PDF/DOI/collection and writing it into Obsidian.
- Creating or updating a paper note under `论文/...`.
- Adding key figures, read-figure notes, highlights, reading心得, citation points, extension directions, or related-topic links to a Zotero-derived note.

Do not use this for generic web summaries when Zotero/PDF access is irrelevant. For ordinary Obsidian edits, use `obsidian-markdown` or `obsidian-cli`.

## Portable Configuration

Resolve machine-specific paths before touching Zotero or Obsidian. Prefer, in order:

1. Explicit paths from the user.
2. Environment variables: `ZOTERO_OBSIDIAN_VAULT`, `ZOTERO_OBSIDIAN_PAPER_ROOT`, `ZOTERO_DATA_DIR`, `ZOTERO_DB`.
3. `skill-config.local.json` next to this `SKILL.md` (user/private, do not package with personal paths).
4. `skill-config.json` template next to this `SKILL.md`.
5. Common OS defaults only after checking they exist and contain data.

Run `python scripts/resolve_config.py --show` to inspect resolved paths. Run `python scripts/smoke_test.py --title "<known Zotero title>"` after installing on a new computer.

Treat the current Codex workspace as staging, not the vault, unless the user explicitly says it is the vault. Never assume a path named `Zotero` or `Obsidian` is valid without checking `zotero.sqlite`, PDF storage, and note root existence.

## Directory Policy

1. Explicit user vault/path/folder wins.
2. A user category name resolves under paper notes root: `论文\<category>`.
3. If no target folder is given, mirror the matched Zotero collection/category under `论文`; create it if missing.
4. If multiple Zotero collections match and the user gave no folder, prefer the collection used to find the item; otherwise choose the most specific and report the choice.
5. If no Zotero collection exists, write under `论文\未分类`.
6. Preserve exact wording: `光` stays `光`; do not normalize to `光学` unless the user says `光学`.
7. Keep category folders clean: paper notes live under `论文\<category>\`, while figure assets live under `论文\_assets\<category>\<paper-slug>\`.
8. If the user corrects the folder/category, move both the note and its `论文\_assets\<category>\<paper-slug>\` assets and update embeds.

## Existing Note Policy

Before creating a note, search the target vault for an existing note in this order:

1. `zotero_item_key` frontmatter or body match.
2. DOI match.
3. Exact title or alias match, including sanitized filename variants.

If a match exists, update that note instead of creating a duplicate. Preserve useful existing sections, frontmatter, links, personal notes, and embeds; add missing metadata, PDF-grounded details, figures, highlights, review cards, and pending questions. If two plausible existing notes match, report the ambiguity before editing.

## Core Workflow

1. Resolve vault, paper root, Zotero data directory, and Zotero database using the portable configuration rules above. If no folder is provided, wait until Zotero lookup reveals the collection.
2. Find the Zotero item by CLI if available, otherwise use `scripts/query_zotero_item.py`; read `references/tools.md` only if you need commands, config details, or SQLite details.
3. Extract metadata, creators, collections, item key, PDF key/path, Zotero child notes, PDF annotations, and PDF/full-text cache.
4. Read the PDF before writing: identify problem, method/model, experiments, key numbers, results, limitations, and future directions.
5. Write or update the note in Chinese unless the user requests otherwise. Match the exemplar style in `references/note-template.md`: compact frontmatter, summary callout, `文献信息`, `关键图`, narrative deep-reading sections, `阅读心得`, `适合引用的观点`, `可延伸方向`, and `关联主题`.
6. Include links: `zotero://select/items/1_<ITEMKEY>` and `zotero://open-pdf/library/items/<PDFKEY>`.
7. Use narrative sections by default. Add compact tables, Mermaid maps, review cards, or `待追问` only when they genuinely improve the note or the user asks for them; do not add decorative filler. Read `references/note-template.md` when drafting the note body.
8. Crop only important figure panels when figures help understanding. For journal PDFs, locate the figure caption start (`Fig. N |`, `Figure N.`) and crop the complete visual region above that caption; add small white padding rather than clipping axis units. Render preview/contact sheets for QA, then remove previews after final embeds. Read `references/tools.md` when cropping.
9. Highlight only conclusions, key numbers, caveats, mechanism mappings, and personal takeaways.
10. Verify final note path, asset embed paths, Zotero links/keys, and cleanup of temp files before reporting.

## Reference Loading

- Read `references/note-template.md` when creating a new note, substantially restructuring a note, or adding tables/Mermaid/review cards.
- Read `references/tools.md` when Zotero CLI is unavailable, path config is needed, metadata/PDF lookup is needed, SQLite details matter, figure crops are requested, or migration smoke tests are needed.
- Use `evals/evals.json` when iterating on this skill.

## Quality Checks

- The note is in the real vault, not the Codex workspace.
- If the user gave no directory, Obsidian category mirrors Zotero collection.
- Category folders contain paper notes, not per-paper asset folders; assets use `论文/_assets/<category>/<paper-slug>/`.
- Metadata and Zotero item/PDF keys are present and clickable.
- Content is PDF-grounded, not only public abstract material.
- The note follows the exemplar style: key figures near the top, figure-specific reading points, narrative explanation, reading心得, citation points, extension directions, and related-topic wikilinks.
- Tables and Mermaid are optional, useful, compact, and not decorative filler.
- Figures are cropped cleanly and embedded with vault-relative wikilinks.
- Figure crops include full axes, units, legends, colorbars, panel labels, and multi-row panels, while excluding caption/body text.
- Preview pages/contact sheets used for cropping are cleaned up unless the user asks to keep them.
- Existing notes are updated rather than duplicated.
- Temporary copied databases, extracted text, preview renders, and contact sheets are removed.
