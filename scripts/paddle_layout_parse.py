#!/usr/bin/env python3
import argparse
import base64
import json
import os
from pathlib import Path
import requests

API_URL = "https://zcr6h3q3mbx5gfg7.aistudio-app.com/layout-parsing"
TOKEN = "9c602580b5711e1a413ec525aaab371938d1248e"


def main():
    ap = argparse.ArgumentParser(description="Call Paddle layout parsing hosted API and save markdown/images")
    ap.add_argument("file", help="Local file path")
    ap.add_argument("--file-type", type=int, choices=[0, 1], help="0=PDF, 1=image; inferred by suffix when omitted")
    ap.add_argument("--output-dir", default="output/paddle-layout", help="Output directory")
    ap.add_argument("--orientation", action="store_true", help="Enable doc orientation classify")
    ap.add_argument("--unwarp", action="store_true", help="Enable doc unwarping")
    ap.add_argument("--chart", action="store_true", help="Enable chart recognition")
    args = ap.parse_args()

    file_path = Path(args.file).expanduser().resolve()
    if not file_path.exists():
        raise SystemExit(f"File not found: {file_path}")

    file_type = args.file_type
    if file_type is None:
        file_type = 0 if file_path.suffix.lower() == '.pdf' else 1

    file_data = base64.b64encode(file_path.read_bytes()).decode("ascii")
    headers = {
        "Authorization": f"token {TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "file": file_data,
        "fileType": file_type,
        "useDocOrientationClassify": args.orientation,
        "useDocUnwarping": args.unwarp,
        "useChartRecognition": args.chart,
    }

    resp = requests.post(API_URL, json=payload, headers=headers, timeout=300)
    print(resp.status_code)
    resp.raise_for_status()
    data = resp.json()
    result = data["result"]

    outdir = Path(args.output_dir).expanduser().resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / 'response.json').write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

    for i, res in enumerate(result.get("layoutParsingResults", [])):
        md_filename = outdir / f"doc_{i}.md"
        md_filename.write_text(res["markdown"]["text"], encoding='utf-8')
        print(f"Markdown document saved at {md_filename}")
        for img_path, img in res["markdown"].get("images", {}).items():
            full_img_path = outdir / img_path
            full_img_path.parent.mkdir(parents=True, exist_ok=True)
            img_bytes = requests.get(img, timeout=120).content
            full_img_path.write_bytes(img_bytes)
            print(f"Image saved to: {full_img_path}")
        for img_name, img in res.get("outputImages", {}).items():
            img_response = requests.get(img, timeout=120)
            if img_response.status_code == 200:
                filename = outdir / f"{img_name}_{i}.jpg"
                filename.write_bytes(img_response.content)
                print(f"Image saved to: {filename}")
            else:
                print(f"Failed to download image, status code: {img_response.status_code}")


if __name__ == "__main__":
    main()
