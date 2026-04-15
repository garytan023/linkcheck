#!/usr/bin/env python3
"""Render all 54 pages of the Honor PDF."""
from pathlib import Path
import pypdfium2 as pdfium

pdf_path = Path('/tmp/openclaw/im-resource-1776267529257-83f49baf-f92b-4ce7-a117-549795baab7d.pdf')
out_dir = Path('/Users/garytan/.openclaw/workspace-dev/tmp/rongyao_review')
out_dir.mkdir(parents=True, exist_ok=True)

pdf = pdfium.PdfDocument(str(pdf_path))
total = len(pdf)
print(f'Rendering {total} pages...')

for idx in range(total):
    page = pdf[idx]
    bmp = page.render(scale=2.0)
    img = bmp.to_pil()
    out = out_dir / f'page_{idx+1:03d}.png'
    img.save(out, 'PNG')
    if (idx + 1) % 10 == 0:
        print(f'  rendered {idx+1}/{total}')

print(f'Done. {total} pages rendered.')
