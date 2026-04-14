#!/usr/bin/env python3
from __future__ import annotations
import json
import re
from pathlib import Path

WORKSPACE = Path('/Users/garytan/Documents/garytan/宇先生/知识库/karpathy-pkm')
MANIFEST_DIR = WORKSPACE / 'manifests' / 'sources'
OUTBOX = WORKSPACE / 'outputs' / 'reports' / 'reference_compile_queue.md'


def extract_text_from_markdown(path: Path) -> str:
    text = path.read_text(encoding='utf-8', errors='ignore')
    text = re.sub(r'^---\n.*?\n---\n', '', text, flags=re.S)
    return text.strip()


def main():
    items = []
    for mf in sorted(MANIFEST_DIR.glob('SRC-*.json')):
        data = json.loads(mf.read_text(encoding='utf-8'))
        src_path = data.get('source_path')
        if not src_path:
            continue
        if data.get('compiled_summary'):
            continue
        p = Path(src_path)
        if not p.exists():
            continue
        text = extract_text_from_markdown(p)
        snippet = text[:1200].replace('\n', ' ')
        items.append({
            'id': data['id'],
            'title': data.get('title'),
            'source_path': src_path,
            'summary': data.get('summary'),
            'snippet': snippet
        })
    OUTBOX.parent.mkdir(parents=True, exist_ok=True)
    lines = ['# Reference Compile Queue', '']
    for it in items:
        lines += [
            f"## {it['id']} {it['title']}",
            f"- source_path: `{it['source_path']}`",
            f"- summary: {it['summary']}",
            '',
            '```text',
            it['snippet'],
            '```',
            ''
        ]
    OUTBOX.write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps({'ok': True, 'queued': len(items), 'output': str(OUTBOX)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
