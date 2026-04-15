#!/usr/bin/env python3
from __future__ import annotations
import json
import os
import re
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

WORKSPACE = Path('/Users/garytan/Documents/garytan/宇先生/知识库/karpathy-pkm')
MANIFEST_DIR = WORKSPACE / 'manifests' / 'sources'
LOG_FILE = WORKSPACE / 'log.md'
LOCAL_OCR_URL = os.environ.get('LOCAL_OCR_URL', 'http://127.0.0.1:8111')
LOCAL_OCR_CLIENT = Path('/Users/garytan/.openclaw/workspace-dev/scripts/local_paddleocr_vl_client.py')


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


def extract_with_pypdf(pdf_path: Path) -> str:
    try:
        from pypdf import PdfReader  # type: ignore
        reader = PdfReader(str(pdf_path))
        texts = []
        for page in reader.pages[:20]:
            texts.append(page.extract_text() or '')
        return clean_text(' '.join(texts))
    except Exception:
        return ''


def render_pdf_preview(pdf_path: Path) -> Path | None:
    tmpdir = Path(tempfile.mkdtemp(prefix='kk-pdf-'))
    out = tmpdir / 'preview.jpg'
    cmd = ['/usr/bin/sips', '-s', 'format', 'jpeg', str(pdf_path), '--out', str(out)]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return out if out.exists() else None
    except Exception:
        return None


def extract_with_local_ocr(pdf_path: Path) -> str:
    preview = render_pdf_preview(pdf_path)
    if not preview or not LOCAL_OCR_CLIENT.exists():
        return ''
    cmd = [
        'python3',
        str(LOCAL_OCR_CLIENT),
        str(preview),
        '--url', LOCAL_OCR_URL,
        '--prompt', '请执行 OCR，提取图片中所有可读文字，尽量保持原有结构。只返回纯文本或 markdown，不要解释。',
        '--max-tokens', '4096'
    ]
    try:
        res = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=180)
        return clean_text(res.stdout)
    except Exception:
        return ''


def main():
    updated = 0
    ocr_pending = 0
    for mf in sorted(MANIFEST_DIR.glob('SRC-*.json')):
        data = json.loads(mf.read_text(encoding='utf-8'))
        tags = data.get('tags') or []
        if 'pdf' not in tags:
            continue
        pdf_path = data.get('file_path')
        if not pdf_path:
            continue
        p = Path(pdf_path)
        if not p.exists():
            continue
        one_line = data.get('summary') or ''
        text = extract_with_pypdf(p)
        extraction_mode = 'pypdf-text'
        if len(text) < 120:
            ocr_text = extract_with_local_ocr(p)
            if ocr_text:
                text = clean_text(ocr_text)
                extraction_mode = 'local-paddleocr-vl'
        if not text:
            data['compiled_summary'] = f"来源《{data.get('title') or p.stem}》PDF 摘要：\n- 一句话摘要：{one_line}\n- [TODO: 待验证] 当前环境缺少可用 OCR 能力，本轮只完成 PDF 入库与 compile 占位。"
            data['concepts'] = sorted(set((data.get('concepts') or []) + ['PDF入库']))
            data['ocr_status'] = 'pending'
            ocr_pending += 1
        else:
            data['compiled_summary'] = summarize_pdf_text(text, data.get('title') or p.stem, one_line)
            data['entities'] = sorted(set((data.get('entities') or []) + keyword_hits(text, ['京东', '腾讯', '阿里', '小红书', '抖音', 'WPP', 'QQ星'])))
            data['concepts'] = sorted(set((data.get('concepts') or []) + keyword_hits(text, ['全渠道营销', '招商方案', '新品', '电商', '投放', '品牌'])))
            data['ocr_status'] = 'done'
        data['compiled_at'] = datetime.now().isoformat()
        data['extraction_mode'] = extraction_mode
        mf.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        updated += 1
    log(f'PDF compile runner 完成：更新 compiled_summary {updated} 条，待 OCR {ocr_pending} 条')
    print(json.dumps({'ok': True, 'updated': updated, 'ocr_pending': ocr_pending}, ensure_ascii=False))


if __name__ == '__main__':
    main()
