#!/usr/bin/env python
"""Render selected PDF crop regions to image files.

Crop boxes are [left, top, right, bottom] measured on a preview rendered at
source_scale. The script renders at --scale and scales the boxes accordingly.
It can also render full-page previews and a contact sheet for locating figures.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


def load_backend() -> tuple[str, Any]:
    try:
        import pypdfium2 as pdfium  # type: ignore

        if hasattr(pdfium, "PdfDocument"):
            return "pdfium", pdfium
    except ModuleNotFoundError:
        pass

    try:
        import fitz  # type: ignore

        return "fitz", fitz
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Missing PDF renderer. Install either pypdfium2 or PyMuPDF/Pillow, e.g. "
            "python -m pip install PyMuPDF Pillow"
        ) from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render cropped figures from a PDF.")
    parser.add_argument("--pdf", required=True, help="Path to the PDF file.")
    parser.add_argument("--out-dir", required=True, help="Directory for output images.")
    parser.add_argument("--crops", default="", help="JSON crop config.")
    parser.add_argument("--preview-pages", default="", help="Pages to render, e.g. 1-3,5.")
    parser.add_argument("--contact-sheet", default="", help="Optional contact sheet image name.")
    parser.add_argument("--scale", type=float, default=3.2, help="PDF render scale.")
    parser.add_argument("--preview-scale", type=float, default=1.2, help="Preview render scale.")
    return parser.parse_args()


def parse_page_spec(value: str) -> list[int]:
    pages: set[int] = set()
    for raw_part in value.split(","):
        part = raw_part.strip()
        if not part:
            continue
        if "-" in part:
            start_text, end_text = (piece.strip() for piece in part.split("-", 1))
            start = int(start_text)
            end = int(end_text)
            if start < 1 or end < start:
                raise SystemExit(f"Invalid page range: {part}")
            pages.update(range(start, end + 1))
        else:
            page = int(part)
            if page < 1:
                raise SystemExit(f"Invalid page number: {part}")
            pages.add(page)
    return sorted(pages)


def preview_name(page_num: int) -> str:
    return f"page-{page_num:03d}.png"


def contact_sheet_columns(count: int) -> int:
    if count < 1:
        return 0
    return min(4, max(1, math.ceil(math.sqrt(count))))


def read_crops(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit("Crop config must be a JSON array.")
    for entry in data:
        if not all(key in entry for key in ("page", "name", "box")):
            raise SystemExit("Each crop needs page, name, and box.")
        if len(entry["box"]) != 4:
            raise SystemExit(f"Crop {entry.get('name', '<unnamed>')} box must have four numbers.")
    return data


def render_page(doc: Any, page_num: int, scale: float) -> Any:
    from PIL import Image

    if isinstance(doc, tuple) and doc[0] == "fitz":
        _, fitz_doc, fitz_module = doc
        page = fitz_doc[page_num - 1]
        pix = page.get_pixmap(matrix=fitz_module.Matrix(scale, scale), alpha=False)
        return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    page = doc[page_num - 1]
    return page.render(scale=scale).to_pil().convert("RGB")


def render_previews(doc: Any, out_dir: Path, pages: list[int], scale: float) -> list[Path]:
    outputs = []
    for page_num in pages:
        output = out_dir / preview_name(page_num)
        image = render_page(doc, page_num, scale)
        image.save(output, optimize=True)
        outputs.append(output)
        print(f"{output}\t{image.size[0]}x{image.size[1]}")
    return outputs


def make_contact_sheet(image_paths: list[Path], output: Path) -> None:
    if not image_paths:
        raise SystemExit("No preview pages rendered for contact sheet.")
    from PIL import Image, ImageDraw

    images = [Image.open(path).convert("RGB") for path in image_paths]
    thumb_width = 360
    label_height = 28
    padding = 12
    thumbnails = []
    for path, image in zip(image_paths, images):
        ratio = thumb_width / image.size[0]
        thumb_height = max(1, round(image.size[1] * ratio))
        thumb = image.resize((thumb_width, thumb_height))
        thumbnails.append((path, thumb))

    columns = contact_sheet_columns(len(thumbnails))
    rows = math.ceil(len(thumbnails) / columns)
    cell_height = max(thumb.size[1] for _, thumb in thumbnails) + label_height
    sheet = Image.new(
        "RGB",
        (columns * (thumb_width + padding) + padding, rows * (cell_height + padding) + padding),
        "white",
    )
    draw = ImageDraw.Draw(sheet)
    for index, (path, thumb) in enumerate(thumbnails):
        row = index // columns
        column = index % columns
        x = padding + column * (thumb_width + padding)
        y = padding + row * (cell_height + padding)
        sheet.paste(thumb, (x, y + label_height))
        draw.text((x, y), path.stem, fill=(0, 0, 0))
    sheet.save(output, optimize=True)
    print(f"{output}\t{sheet.size[0]}x{sheet.size[1]}")


def render_crops(doc: Any, out_dir: Path, crop_path: Path, scale: float) -> None:
    crops = read_crops(crop_path)
    for crop in crops:
        page_num = int(crop["page"])
        name = str(crop["name"])
        source_scale = float(crop.get("source_scale", 1.0))
        factor = scale / source_scale
        box = tuple(round(float(value) * factor) for value in crop["box"])

        image = render_page(doc, page_num, scale)
        cropped = image.crop(box)
        output = out_dir / name
        cropped.save(output, optimize=True)
        print(f"{output}\t{cropped.size[0]}x{cropped.size[1]}")


def main() -> None:
    args = parse_args()
    if not args.crops and not args.preview_pages:
        raise SystemExit("Provide --crops, --preview-pages, or both.")

    backend_name, backend = load_backend()
    pdf_path = Path(args.pdf)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if backend_name == "fitz":
        fitz_doc = backend.open(str(pdf_path))
        doc = ("fitz", fitz_doc, backend)
    else:
        doc = backend.PdfDocument(str(pdf_path))
    preview_outputs: list[Path] = []
    if args.preview_pages:
        preview_outputs = render_previews(doc, out_dir, parse_page_spec(args.preview_pages), args.preview_scale)
        if args.contact_sheet:
            make_contact_sheet(preview_outputs, out_dir / args.contact_sheet)

    if args.crops:
        render_crops(doc, out_dir, Path(args.crops), args.scale)


if __name__ == "__main__":
    main()
