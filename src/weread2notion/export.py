from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .normalize import shelf_entries


def export_weread(client, output_dir: str | Path, fmt: str = "json") -> dict[str, Any]:
    """Export current WeRead shelf data without writing to Notion."""
    if fmt not in {"json", "markdown"}:
        raise ValueError("export format must be json or markdown")
    root = Path(output_dir)
    if root.is_absolute() or ".." in root.parts:
        raise ValueError("output directory must be relative to the current directory")
    root.mkdir(parents=True, exist_ok=True)
    entries = shelf_entries(client.shelf())
    books = []
    for entry in entries:
        bundle = client.book_bundle(entry["bookId"])
        books.append({"entry": entry, "bundle": bundle})
    payload = {"books": books, "count": len(books)}
    (root / "manifest.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if fmt == "markdown":
        books_dir = root / "books"
        books_dir.mkdir(exist_ok=True)
        for item in books:
            entry, bundle = item["entry"], item["bundle"]
            title = str(entry.get("title") or entry.get("bookId") or "未命名")
            safe_title = "".join(c for c in title if c not in '\\/:*?"<>|')[:120]
            lines = [f"# {title}", "", str(bundle.get("info", {}).get("intro") or "")]
            for mark in bundle.get("highlights") or []:
                lines.extend(["", f"> {mark.get('markText') or mark.get('text') or ''}"])
            for note in bundle.get("reviews") or []:
                lines.extend(["", f"**笔记**：{note.get('content') or note.get('review') or ''}"])
            (books_dir / f"{safe_title or '未命名'}.md").write_text(
                "\n".join(lines) + "\n", encoding="utf-8"
            )
    return {"output": str(root), "format": fmt, "books": len(books)}
