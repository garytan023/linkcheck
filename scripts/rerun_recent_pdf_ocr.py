#!/usr/bin/env python3
from __future__ import annotations
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path('/Users/garytan/.openclaw/workspace-dev')
WORKSPACE = Path('/Users/garytan/Documents/garytan/宇先生/知识库/karpathy-pkm')
MANIFEST_DIR = WORKSPACE / 'manifests' / 'sources'
BATCH_SCRIPT = ROOT / 'scripts' / 'paddle_pdf_batch_ocr.py'
PYTHON = ROOT / 'tmp' / 'pdfimg-venv' / 'bin' / 'python'
TARGETS = ['SRC-0089', 'SRC-0090', 'SRC-0091', 'SRC-0092']
PAGE_LIMIT = 12


def clean_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def summarize_page_payload(results: list[dict]) -> str:
    lines = []
    for r in results:
        final_text = (r.get('final_text') or '').strip()
        if not final_text:
            continue
        title = r['image'].split('/')[-1].replace('.png', '')
        snippet = clean_text(final_text)[:220]
        lines.append(f'- {title}: {snippet}')
        if len(lines) >= 8:
            break
    if not lines:
        lines.append('- [TODO: 待验证] 本轮 OCR 没有抽到稳定文本')
    return '\n'.join(lines)


def infer_concepts(title: str, merged: str) -> list[str]:
    mapping = [
        ('618', '618营销节奏'),
        ('全域通', '京东全域通'),
        ('招商', '全链路效果评估'),
        ('新品', '新品上市策略'),
        ('种草', '内容种草'),
        ('跨界', '618跨界联名'),
        ('人群', '人群包投放'),
        ('京东', '京东转化闭环'),
    ]
    found = []
    corpus = f'{title}\n{merged}'
    for needle, concept in mapping:
        if needle in corpus and concept not in found:
            found.append(concept)
    return found[:8]


def infer_entities(title: str, merged: str) -> list[str]:
    candidates = ['京东', '阿里', '阿里妈妈', '小红书', '抖音', 'QQ星', '伊利', '安慕希', '凯度', 'WPP']
    found = []
    corpus = f'{title}\n{merged}'
    for c in candidates:
        if c in corpus and c not in found:
            found.append(c)
    return found[:10]


def run_one(manifest_path: Path) -> dict:
    cmd = [str(PYTHON), str(BATCH_SCRIPT), str(manifest_path), str(PAGE_LIMIT)]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=1200)
    text = res.stdout
    start = text.find('{\n  "manifest"')
    if start == -1:
        raise RuntimeError(f'JSON payload not found for {manifest_path.name}')
    return json.loads(text[start:])


def main():
    updated = []
    for stem in TARGETS:
        manifest_path = MANIFEST_DIR / f'{stem}.json'
        data = json.loads(manifest_path.read_text(encoding='utf-8'))
        result = run_one(manifest_path)
        merged = summarize_page_payload(result['results'])
        title = data.get('title') or stem
        one_line = data.get('summary') or ''
        data['compiled_summary'] = (
            f'来源《{title}》PDF 补强摘要：\n'
            f'- 一句话摘要：{one_line}\n'
            f'- 处理页数：{result.get("processed_pages")}/{result.get("page_count")}\n'
            f'- OCR链路：local-paddleocr-vl + 低文本页图片补强\n'
            f'{merged}'
        )
        data['ocr_status'] = 'done'
        data['extraction_mode'] = 'local-paddleocr-vl+auto-image-enhance'
        data['compiled_at'] = datetime.now().isoformat()
        data['concepts'] = sorted(set((data.get('concepts') or []) + infer_concepts(title, merged)))
        data['entities'] = sorted(set((data.get('entities') or []) + infer_entities(title, merged)))
        data['ocr_page_limit'] = result.get('processed_pages')
        data['ocr_page_count'] = result.get('page_count')
        data['ocr_result_json'] = str((ROOT / 'tmp' / f'{stem.lower()}_ocr_result.json'))
        (ROOT / 'tmp' / f'{stem.lower()}_ocr_result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        manifest_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        updated.append({
            'id': stem,
            'title': title,
            'pages': result.get('processed_pages'),
            'mode': data['extraction_mode'],
            'concepts': data.get('concepts'),
            'entities': data.get('entities'),
        })
    print(json.dumps({'ok': True, 'updated': updated}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
