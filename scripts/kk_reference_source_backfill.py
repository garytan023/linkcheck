#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

WORKSPACE = Path('/Users/garytan/Documents/garytan/宇先生/知识库/karpathy-pkm')
DOC_ROOT = Path('/Users/garytan/Documents/garytan/宇先生/Documents')
MANIFEST_DIR = WORKSPACE / 'manifests' / 'sources'
RAW_ROOT = WORKSPACE / 'raw' / 'obsidian-docs'
INBOX_ROOT = WORKSPACE / 'inbox' / 'obsidian-docs'


def try_match_obsidian_doc(title: str) -> Path | None:
    matches = list(DOC_ROOT.rglob(f'{title}.md'))
    if matches:
        return matches[0]
    return None


def write_stub(target: Path, src: Path, src_id: str, digest: str, summary: str):
    rel = src.relative_to(DOC_ROOT)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        '\n'.join([
            '---',
            f'title: "{src.stem}"',
            'type: obsidian-source-reference',
            f'obsidian_source_path: "{src}"',
            f'obsidian_relative_path: "{rel}"',
            f'content_hash: "{digest}"',
            f'source_id: "{src_id}"',
            '---',
            '',
            f'# {src.stem}',
            '',
            f'- 原文路径: `{src}`',
            f'- 相对路径: `{rel}`',
            f'- 摘要: {summary}',
            '',
            '> reference-only stub',
            ''
        ]),
        encoding='utf-8'
    )


def main():
    updated = 0
    for mf in sorted(MANIFEST_DIR.glob('SRC-*.json')):
        data = json.loads(mf.read_text(encoding='utf-8'))
        if 'obsidian' not in (data.get('tags') or []):
            continue
        if data.get('source_path'):
            continue
        title = data.get('title') or ''
        src = try_match_obsidian_doc(title)
        if not src:
            continue
        rel = src.relative_to(DOC_ROOT)
        data['source_path'] = str(src)
        data['file_path'] = f'obsidian://{src}'
        tags = set(data.get('tags') or [])
        tags.add('reference-only')
        data['tags'] = sorted(tags)
        mf.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        digest = data.get('content_hash') or ''
        summary = data.get('summary') or ''
        write_stub(RAW_ROOT / rel, src, data['id'], digest, summary)
        write_stub(INBOX_ROOT / rel, src, data['id'], digest, summary)
        updated += 1
    print(json.dumps({'ok': True, 'updated': updated}, ensure_ascii=False))


if __name__ == '__main__':
    main()
