#!/usr/bin/env python3
"""Verify Outgunned Adventure role/trope labels exist in the PDF."""

from __future__ import annotations

import sys
from pathlib import Path

import fitz
import yaml

ROOT = Path(__file__).resolve().parent.parent
PDF = ROOT / "docs/outgunned/adventure.pdf"
YAML = ROOT / "data/curated/outgunned_roles.yaml"


def main() -> int:
    if not PDF.exists():
        print(f"Missing PDF: {PDF}", file=sys.stderr)
        return 1
    doc = fitz.open(PDF)
    text = "\n".join(doc[i].get_text() for i in range(doc.page_count))
    with YAML.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    errors: list[str] = []
    for role in data.get("roles") or []:
        label = str(role.get("label", "")).replace("The ", "")
        if label and label not in text:
            errors.append(f"role missing in PDF: {label}")
    for trope in data.get("tropes") or []:
        label = str(trope.get("label", ""))
        if label and label not in text:
            errors.append(f"trope missing in PDF: {label}")
    if errors:
        for e in errors:
            print(e, file=sys.stderr)
        return 1
    print(f"build_outgunned_roles: OK ({len(data.get('roles', []))} roles, {len(data.get('tropes', []))} tropes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
