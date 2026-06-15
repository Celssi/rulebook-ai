"""Layering tests — domain layer must not import API."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"


def _imports_api(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("api"):
            hits.append(f"{path.relative_to(ROOT)}: from {node.module}")
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("api"):
                    hits.append(f"{path.relative_to(ROOT)}: import {alias.name}")
    return hits


def test_src_does_not_import_api() -> None:
    violations: list[str] = []
    for path in SRC.rglob("*.py"):
        violations.extend(_imports_api(path))
    assert not violations, "src/ must not import api/:\n" + "\n".join(violations)
