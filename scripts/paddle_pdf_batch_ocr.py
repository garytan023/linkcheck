#!/usr/bin/env python3
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path('/Users/garytan/.openclaw/workspace-dev')
VENV = ROOT / 'tmp' / 'pdfimg-venv'
PYTHON = VENV / 'bin' / 'python'
PADDLE_SCRIPT = ROOT / 'scripts' / 'paddle_layout_parse.py'
LOCAL_OCR_CLIENT = ROOT / 'scripts' / 'local_paddleocr_vl_client.py'
TMP_IMG_ROOT = ROOT / 'tmp' / 'paddle-pdf-pages'
TMP_OUT_ROOT = ROOT / 'tmp' / 'paddle-pdf-results'
LOW_TEXT_THRESHOLD = 120
DEFAULT_RENDER_SCALE = 3.0
VISION_MAX_TOKENS = 2500


def ensure_env():
    if not PYTHON.exists():
        raise SystemExit('Missing tmp/pdfimg-venv, create it first')


def clean_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def render_pages(pdf_path: Path, page_limit: int, scale: float = DEFAULT_RENDER_SCALE):
    img_dir = TMP_IMG_ROOT / pdf_path.stem
    img_dir.mkdir(parents=True, exist_ok=True)
    code = f'''
from pathlib import Path
import pypdfium2 as pdfium
src = Path(r"{str(pdf_path)}")
outdir = Path(r"{str(img_dir)}")
pdf = pdfium.PdfDocument(str(src))
limit = min({page_limit}, len(pdf))
print('PAGE_COUNT', len(pdf))
for idx in range(limit):
    page = pdf[idx]
    bmp = page.render(scale={scale})
    img = bmp.to_pil()
    out = outdir / f"page_{{idx+1:03d}}.png"
    img.save(out)
    print(out)
'''
    res = subprocess.run([str(PYTHON), '-c', code], capture_output=True, text=True, check=True)
    lines = [x.strip() for x in res.stdout.splitlines() if x.strip()]
    page_count = None
    images = []
    for line in lines:
        if line.startswith('PAGE_COUNT '):
            page_count = int(line.split()[1])
        elif line.endswith('.png'):
            images.append(Path(line))
    return page_count, images


def count_generated_images(outdir: Path) -> int:
    imgs = outdir / 'imgs'
    if not imgs.exists():
        return 0
    return len(list(imgs.glob('*')))


def run_paddle(image_path: Path):
    outdir = TMP_OUT_ROOT / image_path.parent.name / image_path.stem
    outdir.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        sys.executable,
        str(PADDLE_SCRIPT),
        str(image_path),
        '--file-type', '1',
        '--output-dir', str(outdir),
    ], check=True)
    md_path = outdir / 'doc_0.md'
    text = md_path.read_text(encoding='utf-8') if md_path.exists() else ''
    return {
        'image': str(image_path),
        'output_dir': str(outdir),
        'markdown_path': str(md_path) if md_path.exists() else None,
        'text': text,
        'text_length': len(clean_text(text)),
        'detected_image_count': count_generated_images(outdir),
    }


def should_enhance(result: dict) -> bool:
    text_len = result.get('text_length', 0)
    img_count = result.get('detected_image_count', 0)
    return (text_len < LOW_TEXT_THRESHOLD and img_count >= 3) or (text_len < 80 and img_count >= 1)


def run_vision_enhancement(image_path: Path) -> str:
    if not LOCAL_OCR_CLIENT.exists():
        return ''
    prompt = (
        '请阅读这页PDF页面图片，输出简洁 markdown。必须严格只输出下面五段，每段最多3条：\n'
        '## 页面主题\n- ...\n'
        '## 页面主要模块\n- ...\n'
        '## 关键文字\n- ...\n'
        '## 关键数字或对比\n- ...\n'
        '## 业务结论\n- ...\n'
        '要求：不要复读同一句；不要抄提示词；如果这是封面页或章节扉页，就简短输出主题和作用即可；看不清就写“疑似”。'
    )
    try:
        res = subprocess.run([
            'python3',
            str(LOCAL_OCR_CLIENT),
            str(image_path),
            '--prompt', prompt,
            '--max-tokens', str(VISION_MAX_TOKENS),
        ], capture_output=True, text=True, check=True, timeout=180)
        text = sanitize_vision_text(res.stdout.strip())
        return text
    except Exception:
        return ''


def sanitize_vision_text(text: str) -> str:
    if not text:
        return ''
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    banned = ['用一句话概括', '列出2到6个模块', '列出识别到的标题', '只写明确看见的数字', '用1到3条总结', '不要复读', '不要抄提示词']
    filtered = []
    seen = set()
    bullet_count = 0
    for line in lines:
        if any(b in line for b in banned):
            continue
        key = line
        if key in seen:
            continue
        seen.add(key)
        filtered.append(line)
        if line.startswith('- '):
            bullet_count += 1
            if bullet_count >= 12:
                break
        if len(filtered) >= 20:
            break
    text = '\n'.join(filtered).strip()
    if text.count('阿里妈妈') > 8 and '## 页面主题' not in text:
        return ''
    if len(text) > 1200:
        text = text[:1200].rstrip()
    return text


def merge_text_and_vision(ocr_text: str, vision_text: str) -> str:
    ocr_text = (ocr_text or '').strip()
    vision_text = (vision_text or '').strip()
    if vision_text and ocr_text:
        return f"## OCR Text\n\n{ocr_text}\n\n## Vision Summary\n\n{vision_text}"
    if vision_text:
        return f"## Vision Summary\n\n{vision_text}"
    return ocr_text


def main():
    if len(sys.argv) < 2:
        raise SystemExit('Usage: paddle_pdf_batch_ocr.py <manifest.json> [page_limit]')
    ensure_env()
    manifest_path = Path(sys.argv[1]).resolve()
    page_limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    pdf_path = Path(manifest.get('source_path') or manifest.get('file_path'))
    if not pdf_path.exists():
        raise SystemExit(f'PDF not found: {pdf_path}')
    page_count, images = render_pages(pdf_path, page_limit)
    results = []
    for image in images:
        result = run_paddle(image)
        if should_enhance(result):
            vision = run_vision_enhancement(image)
            result['vision_summary'] = vision
            result['enhancement_triggered'] = True
            result['final_text'] = merge_text_and_vision(result.get('text', ''), vision)
        else:
            result['vision_summary'] = ''
            result['enhancement_triggered'] = False
            result['final_text'] = result.get('text', '')
        results.append(result)
    summary = {
        'manifest': str(manifest_path),
        'source_pdf': str(pdf_path),
        'page_count': page_count,
        'processed_pages': len(results),
        'render_scale': DEFAULT_RENDER_SCALE,
        'low_text_threshold': LOW_TEXT_THRESHOLD,
        'results': results,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
