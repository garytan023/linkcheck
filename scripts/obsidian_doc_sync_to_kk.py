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
SOURCES_DIR = WORKSPACE / 'sources'
MANIFEST_DIR = WORKSPACE / 'manifests' / 'sources'
SOURCE_INDEX = WORKSPACE / 'manifests' / 'source_index.csv'
LOG_FILE = WORKSPACE / 'log.md'
REF_EXTS = {'.md'}
COPY_EXTS = {'.pdf'}
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


def summarize_binary(path: Path) -> str:
    kind = path.suffix.lower().lstrip('.') or 'file'
    size_mb = round(path.stat().st_size / 1024 / 1024, 2)
    return f'Obsidian {kind.upper()} 附件入库：{path.stem}（{size_mb} MB）'


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
    if path.suffix.lower() not in (REF_EXTS | COPY_EXTS):
        return True
    if any(path.name.endswith(suf) for suf in SKIP_SUFFIXES):
        return True
    if any(part in SKIP_DIRS for part in path.parts):
        return True
    return False


def collect_files(path_arg: str | None, since_hours: int, limit: int):
    def accept(p: Path):
        return p.is_file() and not should_skip(p)

    if path_arg:
        p = Path(path_arg).expanduser()
        if p.is_file() and accept(p):
            return [p]
        if p.is_dir():
            return [x for x in p.rglob('*') if accept(x)][:limit]
        return []
    cutoff = datetime.now().timestamp() - since_hours * 3600
    files = []
    for p in DOC_ROOT.rglob('*'):
        if not accept(p):
            continue
        try:
            if p.stat().st_mtime >= cutoff:
                files.append(p)
        except FileNotFoundError:
            pass
    return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)[:limit]


def write_reference_stub(target: Path, src: Path, src_id: str | None, digest: str, summary: str):
    target.parent.mkdir(parents=True, exist_ok=True)
    rel = src.relative_to(DOC_ROOT) if DOC_ROOT in src.parents else Path(src.name)
    title = src.stem
    lines = [
        '---',
        f'title: "{title}"',
        'type: obsidian-source-reference',
        f'obsidian_source_path: "{src}"',
        f'obsidian_relative_path: "{rel}"',
        f'content_hash: "{digest}"',
        f'updated_at: "{datetime.fromtimestamp(src.stat().st_mtime).isoformat()}"',
    ]
    if src_id:
        lines.append(f'source_id: "{src_id}"')
    lines += [
        '---',
        '',
        f'# {title}',
        '',
        f'- 原文路径: `{src}`',
        f'- 相对路径: `{rel}`',
        f'- 摘要: {summary}',
        '',
        '> 这是引用型 source stub，不复制正文。编译时应回读原始 Obsidian 文档。',
        ''
    ]
    target.write_text('\n'.join(lines), encoding='utf-8')


def safe_name(text: str) -> str:
    return re.sub(r'[\\/:*?"<>|]+', '_', text)


def ensure_binary_copy(src: Path, src_id: str) -> Path:
    SOURCES_DIR.mkdir(parents=True, exist_ok=True)
    ext = src.suffix.lower()
    dest = SOURCES_DIR / f'{safe_name(src.stem)}_{src_id}{ext}'
    if not dest.exists() or src.stat().st_size != dest.stat().st_size:
        shutil.copy2(src, dest)
    return dest


def build_manifest(base: Path, src_id: str, digest: str, summary: str, mode: str, copied_path: Path | None = None):
    rel = base.relative_to(DOC_ROOT) if DOC_ROOT in base.parents else Path(base.name)
    if mode == 'reference':
        file_path = f'obsidian://{base}'
        source_path = str(base)
        tags = ['obsidian', 'document-sync', 'reference-only']
    else:
        file_path = str(copied_path)
        source_path = str(base)
        tags = ['obsidian', 'document-sync', 'binary-copy', base.suffix.lower().lstrip('.')]
    return {
        'id': src_id,
        'title': base.stem,
        'type': 'other',
        'source_url': None,
        'date_ingested': datetime.now().strftime('%Y-%m-%d'),
        'date_published': None,
        'file_path': file_path,
        'source_path': source_path,
        'obsidian_relative_path': str(rel),
        'content_hash': digest,
        'summary': summary,
        'compiled_summary': None,
        'concepts': [],
        'entities': [],
        'tags': tags,
    }


def main():
    ap = argparse.ArgumentParser(description='Sync Obsidian docs into karpathy-pkm. Markdown uses reference-only mode; PDFs use copied binary mode.')
    ap.add_argument('--since-hours', type=int, default=24)
    ap.add_argument('--limit', type=int, default=200)
    ap.add_argument('--path', help='指定单个文件或目录同步')
    args = ap.parse_args()

    RAW_ROOT.mkdir(parents=True, exist_ok=True)
    INBOX_ROOT.mkdir(parents=True, exist_ok=True)
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    SOURCES_DIR.mkdir(parents=True, exist_ok=True)

    files = collect_files(args.path, args.since_hours, args.limit)
    existing = load_existing_hashes()
    created = 0
    updated = 0
    copied = 0

    for src in files:
        if should_skip(src):
            continue
        base = src if src.is_absolute() else DOC_ROOT / src
        if not base.exists() or not base.is_file():
            continue
        digest = sha256_file(base)
        mode = 'reference' if base.suffix.lower() in REF_EXTS else 'copy'
        summary = summarize_markdown(base) if mode == 'reference' else summarize_binary(base)

        if digest in existing:
            manifest = existing[digest]
            src_id = manifest.get('id')
            updated += 1
        else:
            src_id = next_src_id()
            copied_path = ensure_binary_copy(base, src_id) if mode == 'copy' else None
            manifest = build_manifest(base, src_id, digest, summary, mode, copied_path)
            (MANIFEST_DIR / f'{src_id}.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
            append_source_index(manifest)
            existing[digest] = manifest
            created += 1
            if mode == 'copy':
                copied += 1

        if mode == 'reference':
            raw_stub = RAW_ROOT / base.relative_to(DOC_ROOT)
            inbox_stub = INBOX_ROOT / base.relative_to(DOC_ROOT)
            write_reference_stub(raw_stub, base, src_id, digest, summary)
            write_reference_stub(inbox_stub, base, src_id, digest, summary)

    log(f'Obsidian 同步：扫描 {len(files)} 个文件，新增 manifest {created}，已存在 {updated}，二进制复制 {copied}')
    print(json.dumps({'ok': True, 'scanned': len(files), 'created': created, 'updated_existing': updated, 'copied_binary': copied, 'ref_exts': sorted(REF_EXTS), 'copy_exts': sorted(COPY_EXTS)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
