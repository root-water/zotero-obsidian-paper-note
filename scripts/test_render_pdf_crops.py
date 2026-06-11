#!/usr/bin/env python
"""Regression tests for render_pdf_crops.py helpers."""

from __future__ import annotations

import unittest

import render_pdf_crops


class RenderPdfCropsTest(unittest.TestCase):
    def test_parse_page_spec_supports_ranges_and_deduplicates(self) -> None:
        self.assertEqual([1, 2, 3, 5], render_pdf_crops.parse_page_spec("1-3, 2, 5"))

    def test_parse_page_spec_rejects_invalid_pages(self) -> None:
        with self.assertRaises(SystemExit):
            render_pdf_crops.parse_page_spec("3-1")
        with self.assertRaises(SystemExit):
            render_pdf_crops.parse_page_spec("0")

    def test_preview_name_is_stable_and_sortable(self) -> None:
        self.assertEqual("page-003.png", render_pdf_crops.preview_name(3))

    def test_contact_sheet_columns_are_bounded(self) -> None:
        self.assertEqual(1, render_pdf_crops.contact_sheet_columns(1))
        self.assertEqual(3, render_pdf_crops.contact_sheet_columns(5))
        self.assertEqual(4, render_pdf_crops.contact_sheet_columns(20))


if __name__ == "__main__":
    unittest.main()
