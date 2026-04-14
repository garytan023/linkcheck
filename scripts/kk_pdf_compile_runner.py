#!/usr/bin/env python3
from __future__ import annotations
import json
import re
from datetime import datetime
from pathlib import Path

WORKSPACE = Path('/Users/garytan/Documents/garytan/宇先生/知识库/karpathy-pkm')
MANIFEST_DIR = WORKSPACE / 'manifests' / 'sources'
LOG_FILE = WORKSPACE / 'log.md'


def clean_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def log(msg: str):
    with LOG_FILE.open('a', encoding='utf-8') as f:
        f.write(f"\n- [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")


def summarize_pdf_text(text: str, title: str, one_line: str) -> str:
    parts = re.split(r'(?<=[。！？.!?])\s+', text)
    bullets = []
    for p in parts:
        p = p.strip()
        if len(p) < 20:
            continue
        if p not in bullets:
            bullets.append(p)
        if len(bullets) >= 6:
            break
    if not bullets:
        bullets = [text[:200]] if text else ['[TODO: 待验证] PDF 文本提取结果为空']
    lines = [f'来源《{title}》PDF 摘要：']
    if one_line:
        lines.append(f'- 一句话摘要：{one_line}')
    for b in bullets:
        lines.append(f'- {b[:240]}')
    return '\n'.join(lines)


def keyword_hits(text: str, words: list[str]) -> list[str]:
    out = []
    low = text.lower()
    for w in words:
        if w.lower() in low and w not in out:
            out.append(w)
    return out[:12]


def main():
    updated = 0
    for mf in sorted(MANIFEST_DIR.glob('SRC-*.json')):
        data = json.loads(mf.read_text(encoding='utf-8'))
        tags = data.get('tags') or []
        if 'pdf' not in tags or data.get('compiled_summary'):
            continue
        pdf_path = data.get('file_path')
        if not pdf_path:
            continue
        p = Path(pdf_path)
        if not p.exists():
            continue
        one_line = data.get('summary') or ''
        try:
            # 优先用 PDF tool 外部处理更合适，但这里做本地兜底，读取已存在 OCR/抽取文本不现实时记待补。
            from pypdf import PdfReader  # type: ignore
            reader = PdfReader(str(p))
            text = ' '.join((page.extract_text() or '') for page in reader.pages[:12])
        except Exception:
            text = ''
        text = clean_text(text)
        if not text:
            data['compiled_summary'] = f"来源《{data.get('title') or p.stem}》PDF 摘要：\n- 一句话摘要：{one_line}\n- [TODO: 待验证] 当前仅完成 PDF 入库，需进一步做 OCR/文本抽取后再补强摘要。"
            data['concepts'] = sorted(set((data.get('concepts') or []) + ['PDF入库']))
        else:
            data['compiled_summary'] = summarize_pdf_text(text, data.get('title') or p.stem, one_line)
            data['entities'] = sorted(set((data.get('entities') or []) + keyword_hits(text, ['京东', '腾讯', '阿里', '小红书', '抖音', 'WPP', 'QQ星'])))
            data['concepts'] = sorted(set((data.get('concepts') or []) + keyword_hits(text, ['全渠道营销', '招商方案', '新品', '电商', '投放', '品牌'])))
        data['compiled_at'] = datetime.now().isoformat()
        mf.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        updated += 1
    log(f'PDF compile runner 完成：更新 compiled_summary {updated} 条')
    print(json.dumps({'ok': True, 'updated': updated}, ensure_ascii=False))


if __name__ == '__main__':
    main()
