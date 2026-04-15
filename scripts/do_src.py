#!/usr/bin/env python3
import json, urllib.request, sys
from pathlib import Path

KK = Path("/Users/garytan/Documents/garytan/宇先生/知识库/karpathy-pkm")
MANIFESTS = KK / "manifests" / "sources"
SOURCES = KK / "sources"
BASE_URL = "http://120.24.86.32:3000/anthropic/v1/messages"
API_KEY = "sk-cp-051e6b5bed14b6801c71936fcf9c58a868bf8e35d1f9e90d55236d296630ea18"
MODEL = "MiniMax-M2.7-highspeed"

def call_llm(content, src_id):
    prompt = f"来源ID: {src_id}\n\n{content[:4000]}"
    payload = {
        "model": MODEL, "max_tokens": 1500,
        "system": "你是营销案例分析师。从文档提取JSON格式摘要（严格返回JSON，不要markdown格式）：{\"summary\":\"一句话摘要(50字内)\",\"compiled_summary\":\"完整摘要(200字内)\",\"concepts\":[\"概念\"],\"entities\":[\"品牌\"],\"tags\":[\"标签\"]}",
        "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
    }
    req = urllib.request.Request(BASE_URL, data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode())
            text = ""
            for block in result.get("content", []):
                if block.get("type") == "text":
                    text = block.get("text", "").strip()
                    break
            if not text:
                for block in result.get("content", []):
                    if block.get("type") == "thinking":
                        text = block.get("thinking", "").strip()
                        break
            if not text:
                return None
            # Parse JSON - handle raw JSON without markdown
            text = text.strip()
            # Remove markdown code blocks if present
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(lines[1:])  # Remove first line (```json)
                text = text.rsplit("```", 1)[0]  # Remove last line (```)
                text = text.strip()
            return json.loads(text)
    except Exception as e:
        print(f"API error {src_id}: {e}", file=sys.stderr)
        return None

src_ids = sys.argv[1:]
for src_id in src_ids:
    mf = MANIFESTS / f"{src_id}.json"
    if not mf.exists():
        print(f"SKIP {src_id}: no manifest", file=sys.stderr)
        continue
    manifest = json.load(open(mf))
    fp = manifest.get("file_path", "")
    src_path = KK / fp
    if not src_path.exists():
        print(f"SKIP {src_id}: no source at {fp}", file=sys.stderr)
        continue
    content = src_path.read_text(encoding="utf-8", errors="replace")
    print(f"Processing {src_id} ({len(content)} chars)...", file=sys.stderr, flush=True)
    result = call_llm(content, src_id)
    if result:
        manifest["summary"] = result.get("summary", "")
        manifest["compiled_summary"] = result.get("compiled_summary", "")
        manifest["concepts"] = result.get("concepts", [])
        manifest["entities"] = result.get("entities", [])
        manifest["tags"] = result.get("tags", [])
        manifest["compiled_at"] = "2026-04-15T06:30:00+08:00"
        json.dump(manifest, open(mf, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"DONE {src_id}", flush=True)
    else:
        print(f"FAIL {src_id}", flush=True)
