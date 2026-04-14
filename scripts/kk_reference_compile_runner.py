#!/usr/bin/env python3
from __future__ import annotations
import json
import re
from datetime import datetime
from pathlib import Path

WORKSPACE = Path('/Users/garytan/Documents/garytan/宇先生/知识库/karpathy-pkm')
MANIFEST_DIR = WORKSPACE / 'manifests' / 'sources'
LOG_FILE = WORKSPACE / 'log.md'


def clean_markdown(text: str) -> str:
    text = re.sub(r'^---\n.*?\n---\n', '', text, flags=re.S)
    text = re.sub(r'```.*?```', ' ', text, flags=re.S)
    text = re.sub(r'!\[[^\]]*\]\([^\)]*\)', ' ', text)
    text = re.sub(r'\[([^\]]+)\]\([^\)]*\)', r'\1', text)
    text = re.sub(r'[#>*`\-]{1,3}', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def sentence_split(text: str):
    parts = re.split(r'(?<=[。！？.!?])\s+', text)
    return [p.strip() for p in parts if p.strip()]


def make_compiled_summary(title: str, summary: str, text: str) -> str:
    sents = sentence_split(text)
    bullets = []
    for s in sents:
        if len(s) < 18:
            continue
        if s not in bullets:
            bullets.append(s)
        if len(bullets) >= 6:
            break
    if not bullets and text:
        bullets = [text[:180]]
    lines = [f'来源《{title}》摘要：']
    if summary:
        lines.append(f'- 一句话摘要：{summary}')
    for b in bullets:
        lines.append(f'- {b[:220]}')
    return '\n'.join(lines)


def extract_entities(text: str):
    found = []
    for kw in ['Claude Code', 'Obsidian', 'Seedance', '飞书', '微信', '小红书', '京东', '腾讯广告', 'AI', 'Agent']:
        if kw.lower() in text.lower() and kw not in found:
            found.append(kw)
    return found[:10]


def extract_concepts(text: str):
    found = []
    for kw in ['工作流', '自动化', '知识库', '视频生成', '数字人', '提示词', '并发', '复购', '媒介投放', '内容营销']:
        if kw in text and kw not in found:
            found.append(kw)
    return found[:10]


def log(msg: str):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open('a', encoding='utf-8') as f:
        f.write(f"\n- [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")


def main():
    updated = 0
    for mf in sorted(MANIFEST_DIR.glob('SRC-*.json')):
        data = json.loads(mf.read_text(encoding='utf-8'))
        src_path = data.get('source_path')
        if not src_path or data.get('compiled_summary'):
            continue
        p = Path(src_path)
        if not p.exists():
            continue
        raw = p.read_text(encoding='utf-8', errors='ignore')
        text = clean_markdown(raw)
        if not text:
            continue
        data['compiled_summary'] = make_compiled_summary(data.get('title') or p.stem, data.get('summary') or '', text)
        data['entities'] = sorted(set((data.get('entities') or []) + extract_entities(text)))
        data['concepts'] = sorted(set((data.get('concepts') or []) + extract_concepts(text)))
        data['compiled_at'] = datetime.now().isoformat()
        mf.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        updated += 1
    log(f'reference compile runner 完成：更新 compiled_summary {updated} 条')
    print(json.dumps({'ok': True, 'updated': updated}, ensure_ascii=False))


if __name__ == '__main__':
    main()
