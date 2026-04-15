#!/usr/bin/env python3
import subprocess, sys
from pathlib import Path

SCRIPT = "/Users/garytan/.openclaw/workspace-dev/scripts/local_paddleocr_vl_client.py"
OUTDIR = Path("/Users/garytan/.openclaw/workspace-dev/tmp/rongyao_review")

for i in [1, 2, 3]:
    page_file = OUTDIR / f"page_{i:03d}.png"
    print(f"\n=== PAGE {i} ===")
    result = subprocess.run(
        ["python3", SCRIPT, str(page_file),
         "--prompt", "请执行OCR并理解这张PPT/PDF页面内容，输出markdown，保留标题、模块名、关键结论。用中文输出。",
         "--max-tokens", "2500"],
        capture_output=True, text=True, timeout=120
    )
    print(result.stdout[:1500] if result.stdout else "(empty)")
    if result.stderr:
        print(f"[stderr] {result.stderr[:200]}")
