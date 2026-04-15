#!/usr/bin/env python3
"""
kk ingest — 收录来源文件到研究 workspace

Usage:
    python3 kk_ingest.py <workspace-path> <source-path>
    python3 kk_ingest.py <workspace-path> --inbox

Features:
    - 复制到 sources/
    - 生成 SRC-NNNN.json manifest
    - 更新 source_index.csv
    - SHA-256 去重
"""

import sys
import json
import csv
import hashlib
import shutil
from pathlib import Path
from datetime import datetime

SUPPORTED = {".md", ".txt", ".pdf", ".html", ".htm"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def next_id(ws: Path) -> str:
    ids = []
    for f in (ws / "manifests" / "sources").glob("SRC-*.json"):
        try:
            ids.append(int(f.stem.split("-")[1]))
        except (IndexError, ValueError):
            pass
    return f"SRC-{(max(ids) + 1) if ids else 1:04d}"


def extract_title(path: Path) -> str:
    if path.suffix == ".md":
        try:
            for line in open(path, encoding="utf-8", errors="ignore"):
                line = line.strip()
                if line.startswith("# "):
                    return line[2:].strip()
        except Exception:
            pass
    return path.stem.replace("-", " ").replace("_", " ").title()


def create_manifest(ws: Path, src_id: str, path: Path) -> dict:
    h = sha256(path)
    title = extract_title(path)
    rel = f"sources/{path.name}"
    manifest = {
        "id": src_id,
        "title": title,
        "type": "article",
        "source_url": None,
        "date_ingested": datetime.now().strftime("%Y-%m-%d"),
        "date_published": None,
        "file_path": rel,
        "content_hash": h,
        "summary": None,
        "compiled_summary": None,
        "concepts": [],
        "entities": [],
        "tags": []
    }

    # 去重
    idx = ws / "manifests" / "source_index.csv"
    if idx.exists():
        with open(idx, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("content_hash") == h:
                    print(f"  ⚠️  相同内容已存在（hash 匹配），跳过: {path.name}")
                    return None

    # 复制
    dest = ws / "sources" / path.name
    if dest.exists():
        dest = ws / "sources" / f"{path.stem}_{src_id}{path.suffix}"
    shutil.copy2(path, dest)

    # manifest
    manifest["file_path"] = f"sources/{dest.name}"
    mp = ws / "manifests" / "sources" / f"{src_id}.json"
    with open(mp, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    # index
    with open(idx, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([src_id, title, "article",
                                 datetime.now().strftime("%Y-%m-%d"),
                                 manifest["file_path"], h])

    print(f"  ✅ {src_id}: {title}")
    return manifest


def ingest_file(ws: Path, path: Path) -> bool:
    if path.suffix.lower() not in SUPPORTED:
        print(f"  ⚠️  不支持: {path.name}")
        return False
    if not path.exists():
        print(f"  ❌ 文件不存在: {path}")
        return False
    src_id = next_id(ws)
    m = create_manifest(ws, src_id, path)
    return m is not None


def ingest_inbox(ws: Path) -> tuple[int, int]:
    inbox = ws / "inbox"
    files = [f for f in inbox.iterdir() if f.is_file() and f.suffix.lower() in SUPPORTED]
    if not files:
        print("  inbox 为空")
        return 0, 0
    ok, skip = 0, 0
    for f in sorted(files):
        if ingest_file(ws, f):
            ok += 1
            done = inbox / ".done"
            done.mkdir(exist_ok=True)
            f.rename(done / f.name)
        else:
            skip += 1
    return ok, skip


def print_status(ws: Path):
    idx = ws / "manifests" / "source_index.csv"
    n = 0
    if idx.exists():
        with open(idx, encoding="utf-8") as f:
            n = sum(1 for _ in f) - 1
    wiki_n = len(list((ws / "wiki" / "concepts").glob("*.md"))) + \
             len(list((ws / "wiki" / "entities").glob("*.md")))
    print(f"\n[kk] {ws.name} | 来源: {n} | wiki: {wiki_n} 页 | 等待 compile")


def main():
    if len(sys.argv) < 2:
        print("Usage: kk_ingest.py <workspace-path> <source-path>")
        print("       kk_ingest.py <workspace-path> --inbox")
        sys.exit(1)

    ws = Path(sys.argv[1])
    if not (ws / "AGENTS.md").exists():
        print(f"❌ 不是有效的 kk workspace: {ws}")
        sys.exit(1)

    print(f"📥 Ingest: {ws.name}\n")

    if "--inbox" in sys.argv:
        ok, skip = ingest_inbox(ws)
    elif len(sys.argv) >= 3:
        src = Path(sys.argv[2])
        if ingest_file(ws, src):
            ok, skip = 1, 0
        else:
            ok, skip = 0, 1
    else:
        print("❌ 缺少来源路径")
        sys.exit(1)

    print(f"\n完成: {ok} 个成功，{skip} 个跳过")
    print_status(ws)

    # append log
    if ok > 0:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        log = ws / "log.md"
        log.open("a", encoding="utf-8").write(f"## [{ts}] ingest | {ok}个来源\n")


if __name__ == "__main__":
    main()
