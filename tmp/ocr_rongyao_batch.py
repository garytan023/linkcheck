#!/usr/bin/env python3
"""
Full pipeline for Honor PDF (54 pages):
1. Batch OCR all 54 pages
2. Detect low-text pages (trigger image enhancement)
3. Compile summary + concepts
4. Write manifest to karpathy-pkm
5. Write Obsidian entry
"""
import json, re, subprocess, sys, textwrap
from datetime import datetime
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────────
PAGES_DIR  = Path('/Users/garytan/.openclaw/workspace-dev/tmp/rongyao_review')
PDF_PATH   = Path('/tmp/openclaw/im-resource-1776267529257-83f49baf-f92b-4ce7-a117-549795baab7d.pdf')
KK_ROOT    = Path('/Users/garytan/Documents/garytan/宇先生/知识库/karpathy-pkm')
MANIFEST   = KK_ROOT / 'manifests/sources/SRC-0100.json'
OCR_CLIENT = Path('/Users/garytan/.openclaw/workspace-dev/scripts/local_paddleocr_vl_client.py')
OCR_URL    = 'http://127.0.0.1:8111'
OBSIDIAN_DIR = Path('/Users/garytan/Documents/garytan/宇先生/Inbox')

MANIFEST_NUM = '0100'
TITLE       = '京东荣耀手机 25年全年Review'
ONE_LINE    = 'WPP Media 为荣耀手机在京东平台开展的2025全年付费投放复盘报告，覆盖付费概况、25年洞察、26年方向及新品复盘'

# ── Helpers ─────────────────────────────────────────────────────────────────
def run_ocr(page_path: Path, page_num: int) -> tuple[str, int]:
    """Returns (text, text_len)."""
    prompt = (
        "请执行OCR并理解这张PPT/PDF页面内容，输出markdown，保留标题、模块名、关键结论。用中文输出。"
        "只返回markdown内容，不要解释。"
    )
    try:
        res = subprocess.run(
            ['python3', str(OCR_CLIENT), str(page_path),
             '--prompt', prompt, '--max-tokens', '3000'],
            capture_output=True, text=True, timeout=120
        )
        text = res.stdout.strip()
        # Strip any leading/trailing markdown fences
        text = re.sub(r'^```markdown\s*', '', text)
        text = re.sub(r'^```\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
        return text, len(text)
    except Exception as e:
        return f'[OCR错误 page {page_num}: {e}]', 0

def detect_low_text(text: str, page_num: int) -> bool:
    """True if page should be re-processed with image enhancement."""
    # Pages that are likely mostly images/charts
    if len(text) < 80:
        return True
    # Pages with lots of numbers but little prose (data-heavy slides)
    digits = sum(c.isdigit() for c in text)
    return digits > 200 and len(text) < 150

def enhance_low_text_page(page_path: Path, page_num: int) -> str:
    """Run image-enhanced OCR on a low-text page."""
    prompt = (
        "这是一张图片/图表页面。请仔细看图，描述图中所有可见内容："
        "标题、坐标轴标签、图例说明、数据趋势、关键数字、结论文字等。"
        "用中文详细输出，markdown格式。"
    )
    try:
        res = subprocess.run(
            ['python3', str(OCR_CLIENT), str(page_path),
             '--prompt', prompt, '--max-tokens', '3000'],
            capture_output=True, text=True, timeout=120
        )
        return res.stdout.strip()
    except:
        return '[图片增强OCR失败]'

def extract_keywords(text: str) -> list[str]:
    """Extract relevant concepts from text."""
    word_sets = {
        '京东': ['京东', 'JD', 'jd.com'],
        '荣耀': ['荣耀', 'Honor', 'honor'],
        'WPP': ['WPP'],
        '小红书': ['小红书', 'XHS'],
        '抖音': ['抖音', 'TikTok'],
        '阿里': ['阿里', '淘宝', '天猫'],
        '电商': ['电商', '平台投放', '付费投放'],
        '投放': ['投放', '竞价', 'CPC', 'CPM', 'ROI', 'ROAS', '付费'],
        '新品': ['新品', '新客', '新品上市'],
        '品牌': ['品牌', 'Brand'],
        '全年': ['全年', 'Y25', '25年', '2025'],
        '复盘': ['复盘', 'Review', 'review', '回顾'],
        '洞察': ['洞察', '趋势', '机会点'],
        '方向': ['方向', '策略', '26年', '2026'],
        '营销': ['营销', '节点', '大促', '618', '双11'],
    }
    hits = []
    low = text.lower()
    for concept, keywords in word_sets.items():
        for kw in keywords:
            if kw.lower() in low:
                hits.append(concept)
                break
    return sorted(set(hits))[:20]

# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    total_pages = 54
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Starting OCR for {total_pages} pages...')

    all_results = []   # (page_num, text, mode)
    low_text_pages = []

    # Pass 1: OCR all pages
    for i in range(1, total_pages + 1):
        page_path = PAGES_DIR / f'page_{i:03d}.png'
        if not page_path.exists():
            print(f'  [WARN] Page {i} image not found, skipping')
            continue
        text, text_len = run_ocr(page_path, i)
        all_results.append((i, text, text_len))
        if i % 10 == 0:
            print(f'  [{datetime.now().strftime("%H:%M:%S")}] OCRed pages 1-{i}')
        if detect_low_text(text, i):
            low_text_pages.append(i)
        sys.stdout.flush()

    print(f'\n[{datetime.now().strftime("%H:%M:%S")}] Low-text pages: {low_text_pages}')

    # Pass 2: Image enhancement for low-text pages
    for i in low_text_pages:
        page_path = PAGES_DIR / f'page_{i:03d}.png'
        enhanced = enhance_low_text_page(page_path, i)
        # Replace in results
        for idx, (pn, txt, lnm) in enumerate(all_results):
            if pn == i:
                all_results[idx] = (i, enhanced, len(enhanced))
                break
        print(f'  Enhanced page {i} ({len(enhanced)} chars)')

    # Compile full text
    full_text = '\n\n'.join(f'--- Page {pn} ---\n{txt}' for pn, txt, _ in all_results)

    # Build summary (first 8 pages content for title/intro, last pages for conclusions)
    intro_pages = [txt for pn, txt, _ in all_results if pn <= 5]
    intro_text = '\n\n'.join(intro_pages)
    # Extract structured sections
    summary_parts = []
    # Try to find section headers
    for pn, txt, _ in all_results:
        if re.search(r'^#{1,3}\s+(?:目录|摘要|总结|概览|全年|付费|洞察|方向|新品|复盘)', txt, re.M):
            summary_parts.append(f'Page {pn}: {txt[:300]}')
        if len(summary_parts) >= 8:
            break

    concepts = extract_keywords(full_text)

    # Build compiled_summary
    summary_lines = [f'## 来源《{TITLE}》PDF 摘要']
    summary_lines.append(f'**一句话摘要**：{ONE_LINE}')
    summary_lines.append(f'**总页数**：{total_pages}页')
    summary_lines.append(f'**关键词**：{", ".join(concepts)}')
    if summary_parts:
        summary_lines.append('\n### 各章节内容预览')
        for part in summary_parts[:8]:
            summary_lines.append(f'- {part}')
    summary_lines.append(f'\n*本摘要由本地OCR提取+AI整理，完整原始文本见 raw sources.*')

    compiled_summary = '\n'.join(summary_lines)

    # ── Write manifest ───────────────────────────────────────────────────────
    manifest_data = {
        'id': 'SRC-0100',
        'title': TITLE,
        'source_type': 'pdf',
        'file_path': str(PDF_PATH),
        'page_count': total_pages,
        'summary': ONE_LINE,
        'compiled_summary': compiled_summary,
        'concepts': concepts,
        'entities': ['荣耀/Honor', '京东', 'WPP Media', '荣耀京东自营旗舰店'],
        'tags': ['pdf', '荣耀', '京东', 'WPP', '2025', '全年复盘', '付费投放'],
        'source_date': '2025',
        'ocr_status': 'done',
        'extraction_mode': 'local-paddleocr-vl (54 pages)',
        'low_text_pages_enhanced': low_text_pages,
        'compiled_at': datetime.now().isoformat(),
    }

    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest_data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'\n✅ Manifest written: {MANIFEST}')

    # ── Write Obsidian entry ────────────────────────────────────────────────
    obs_content = f"""---
title: {TITLE}
date: 2025
tags:
  - 荣耀
  - 京东
  - WPP
  - 2025复盘
  - 付费投放
  - 电商
source: SRC-0100
ocr_status: done
---

# {TITLE}

## 一句话摘要
{ONE_LINE}

## 关键词
{', '.join(concepts)}

## 低文本页（已图片增强）
{', '.join(f'Page {p}' for p in low_text_pages) if low_text_pages else '无'}

## 内容预览

{compiled_summary}

---

*原始PDF页数：{total_pages}页 | OCR提取+AI整理 | 来自 karpathy-pkm SRC-0100*
"""
    obs_path = OBSIDIAN_DIR / f'SRC-0100_荣耀京东Y25全年Review.md'
    obs_path.write_text(obs_content, encoding='utf-8')
    print(f'✅ Obsidian entry written: {obs_path}')

    print(f'''
╔══════════════════════════════════════╗
║  ✅ Honor PDF 入库完成               ║
╠══════════════════════════════════════╣
║  Manifest: SRC-0100.json             ║
║  Obsidian: SRC-0100_荣耀京东Y25全年  ║
║  总页数: {total_pages}页                        ║
║  OCR页数: {total_pages - len(low_text_pages)}页（直接）+ {len(low_text_pages)}页（图片增强）  ║
║  关键词: {', '.join(concepts[:8])}...  ║
╚══════════════════════════════════════╝
''')

if __name__ == '__main__':
    main()
