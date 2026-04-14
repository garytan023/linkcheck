#!/usr/bin/env python3
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import re
import shutil
from datetime import datetime
from pathlib import Path

WORKSPACE = Path('/Users/garytan/Documents/garytan/宇先生/知识库/karpathy-pkm')
DOC_ROOT = Path('/Users/garytan/Documents/garytan/宇先生/Documents')
RAW_ROOT = WORKSPACE / 'raw' / 'obsidian-docs'
INBOX_ROOT = WORKSPACE / 'inbox' / 'obsidian-docs'
MANIFEST_DIR = WORKSPACE / 'manifests' / 'sources'
SOURCE_INDEX = WORKSPACE / 'manifests' / 'source_index.csv'
LOG_FILE = WORKSPACE / 'log.md'
EXT_ALLOW = {'.md'}
SKIP_DIRS = {'.obsidian', '.trash', '.git'}
SKIP_SUFFIXES = {'.excalidraw.md'}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def load_existing_hashes() -> dict[str, dict]:
    results = {}
    if not MANIFEST_DIR.exists():
        return results
    for p in MANIFEST_DIR.glob('SRC-*.json'):
        try:
            data = json.loads(p.read_text(encoding='utf-8'))
            ch = data.get('content_hash')
            if ch:
                results[ch] = data
        except Exception:
            continue
    return results


def next_src_id() -> str:
    nums = []
    for p in MANIFEST_DIR.glob('SRC-*.json'):
        m = re.match(r'SRC-(\d+)\.json$', p.name)
        if m:
            nums.append(int(m.group(1)))
    return f'SRC-{max(nums, default=0) + 1:04d}'


def summarize_markdown(path: Path, max_len: int = 80) -> str:
    text = path.read_text(encoding='utf-8', errors='ignore')
    text = re.sub(r'^---\n.*?\n---\n', '', text, flags=re.S)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for ln in lines:
        if ln.startswith('#'):
            continue
        if len(ln) >= 8:
            return ln[:max_len]
    return f'Obsidian 文档同步入库：{path.stem}'


def append_source_index(row: dict):
    SOURCE_INDEX.parent.mkdir(parents=True, exist_ok=True)
    exists = SOURCE_INDEX.exists()
    fields = ['id', 'title', 'type', 'source_url', 'date_ingested', 'date_published', 'file_path', 'content_hash', 'summary']
    with SOURCE_INDEX.open('a', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if not exists:
            w.writeheader()
        w.writerow({k: row.get(k, '') for k in fields})


def log(msg: str):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with LOG_FILE.open('a', encoding='utf-8') as f:
        f.write(f'\n- [{ts}] {msg}')


def should_skip(path: Path) -> bool:
    if path.suffix not in EXT_ALLOW:
        return True
    if any(path.name.endswith(suf) for suf in SKIP_SUFFIXES):
        return True
    if any(part in SKIP_DIRS for part in path.parts):
        return True
    return False


def collect_files(path_arg: str | None, since_hours: int, limit: int):
    if path_arg:
        p = Path(path_arg).expanduser()
        if p.is_file():
            return [p]
        if p.is_dir():
            return [x for x in p.rglob('*.md') if not should_skip(x)][:limit]
        return []
    cutoff = datetime.now().timestamp() - since_hours * 3600
    files = []
    for p in DOC_ROOT.rglob('*.md'):
        if should_skip(p):
            continue
        try:
            if p.stat().st_mtime >= cutoff:
                files.append(p)
        except FileNotFoundError:
            pass
    return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)[:limit]


def main():
    ap = argparse.ArgumentParser(description='Sync Obsidian docs to karpathy-pkm raw/inbox and create manifests.')
    ap.add_argument('--since-hours', type=int, default=24)
    ap.add_argument('--limit', type=int, default=200)
    ap.add_argument('--path', help='指定单个文件或目录同步')
    args = ap.parse_args()

    RAW_ROOT.mkdir(parents=True, exist_ok=True)
    INBOX_ROOT.mkdir(parents=True, exist_ok=True)
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)

    files = collect_files(args.path, args.since_hours, args.limit)
    existing = load_existing_hashes()
    created = 0
    updated = 0

    for src in files:
        if should_skip(src):
            continue
        base = src if src.is_absolute() else DOC_ROOT / src
        if not base.exists() or not base.is_file():
            continue
        digest = sha256_file(base)
        rel = base.relative_to(DOC_ROOT) if DOC_ROOT in base.parents else Path(base.name)
        raw_dest = RAW_ROOT / rel
        inbox_dest = INBOX_ROOT / rel
        raw_dest.parent.mkdir(parents=True, exist_ok=True)
        inbox_dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(base, raw_dest)
        shutil.copy2(base, inbox_dest)
        if digest in existing:
            updated += 1
            continue
        src_id = next_src_id()
        source_copy = WORKSPACE / 'sources' / f'{base.stem}_{src_id}.md'
        source_copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(base, source_copy)
        manifest = {
            'id': src_id,
            'title': base.stem,
            'type': 'other',
            'source_url': None,
            'date_ingested': datetime.now().strftime('%Y-%m-%d'),
            'date_published': None,
            'file_path': str(source_copy.relative_to(WORKSPACE)),
            'content_hash': digest,
            'summary': summarize_markdown(base),
            'compiled_summary': None,
            'concepts': [],
            'entities': [],
            'tags': ['obsidian', 'document-sync'],
        }
        (MANIFEST_DIR / f'{src_id}.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
        append_source_index(manifest)
        existing[digest] = manifest
        created += 1

    log(f'Obsidian 文档同步：扫描 {len(files)} 个文档，新增 manifest {created}，已存在内容 {updated}')
    print(json.dumps({'ok': True, 'scanned': len(files), 'created': created, 'updated_existing': updated, 'raw_root': str(RAW_ROOT), 'inbox_root': str(INBOX_ROOT)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
