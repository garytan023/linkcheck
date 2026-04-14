---
name: paddle-layout
version: 0.1.0
description: Use hosted Paddle layout parsing API to convert PDFs or images into structured Markdown with extracted images. Best for OCR + layout reconstruction of reports, decks, scanned PDFs, and screenshots.
---

# Paddle Layout Parsing

Use the hosted Paddle layout parsing API through the local helper script.

## When to use

- PDF OCR with layout preserved
- Image to structured Markdown
- Scanned reports / PPT exports / screenshots
- When local Tesseract OCR is unreliable for Chinese mixed-content docs

## Script

`/Users/garytan/.openclaw/workspace-dev/scripts/paddle_layout_parse.py`

## Usage

### PDF
```bash
python3 scripts/paddle_layout_parse.py "/path/to/file.pdf"
```

### Image
```bash
python3 scripts/paddle_layout_parse.py "/path/to/file.png" --file-type 1
```

### Custom output directory
```bash
python3 scripts/paddle_layout_parse.py "/path/to/file.pdf" --output-dir tmp/paddle-run
```

## Output

The output directory contains:
- `doc_0.md` etc. for Markdown text
- downloaded embedded images
- output visualization images
- `response.json` raw API response

## Important notes

- This sends the file content to an external hosted API.
- Use for non-sensitive or approved materials.
- Prefer this over local OCR when the goal is usable Markdown structure, especially for Chinese PDFs.
