#!/usr/bin/env python3
from __future__ import annotations
import argparse
import base64
import json
from pathlib import Path
from urllib import request


def to_data_url(path: Path) -> str:
    mime = 'image/png'
    suf = path.suffix.lower()
    if suf in {'.jpg', '.jpeg'}:
        mime = 'image/jpeg'
    elif suf == '.webp':
        mime = 'image/webp'
    data = base64.b64encode(path.read_bytes()).decode('ascii')
    return f'data:{mime};base64,{data}'


def call_server(image_path: Path, url: str, prompt: str, model: str | None = None, max_tokens: int = 2048, timeout: int = 120) -> str:
    body = {
        'messages': [
            {
                'role': 'user',
                'content': [
                    {'type': 'text', 'text': prompt},
                    {'type': 'image_url', 'image_url': {'url': to_data_url(image_path)}}
                ]
            }
        ],
        'temperature': 0,
        'max_tokens': max_tokens,
        'stream': False,
    }
    if model:
        body['model'] = model
    req = request.Request(
        url.rstrip('/') + '/v1/chat/completions',
        data=json.dumps(body).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    with request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode('utf-8', errors='replace'))
    return data['choices'][0]['message']['content'].strip()


def main():
    ap = argparse.ArgumentParser(description='Call local llama-server PaddleOCR-VL endpoint with one image')
    ap.add_argument('image')
    ap.add_argument('--url', default='http://127.0.0.1:8111')
    ap.add_argument('--model', default='')
    ap.add_argument('--prompt', default='请执行 OCR，提取图片中所有可读文字，尽量保持原有结构。只返回纯文本或 markdown，不要解释。')
    ap.add_argument('--max-tokens', type=int, default=2048)
    args = ap.parse_args()

    image = Path(args.image).expanduser().resolve()
    text = call_server(image, args.url, args.prompt, args.model or None, args.max_tokens)
    print(text)


if __name__ == '__main__':
    main()
