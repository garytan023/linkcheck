#!/usr/bin/env python3
"""
Extract compiled_summary for ISV sources using MiniMax API.
Processes all 11 sources in one go.
"""
import json, os, sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

# ── Config ──────────────────────────────────────────────────────────────
KK = Path("/Users/garytan/Documents/garytan/宇先生/知识库/karpathy-pkm")
MANIFESTS = KK / "manifests" / "sources"
SOURCES = KK / "sources"

BASE_URL = "http://120.24.86.32:3000/anthropic/v1/messages"
API_KEY  = "sk-cp-051e6b5bed14b6801c71936fcf9c58a868bf8e35d1f9e90d55236d296630ea18"
MODEL    = "MiniMax-M2.7-highspeed"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "Anthro-Beta": "interleaved-thinking-2025-05-14",
}

SYSTEM_PROMPT = """你是一个专业的营销案例分析师。你的任务是从来源文档中提取结构化的案例摘要。

请从文档中提取以下信息并返回JSON格式（不要加代码块标记）：
{
  "summary": "一句话摘要（50字内）",
  "compiled_summary": "完整摘要（200字内，包含关键数据/洞察、方法论、结果）",
  "concepts": ["核心概念标签1", "核心概念标签2"],
  "entities": ["关键品牌/产品/平台/代理商"],
  "tags": ["补充标签"]
}

注意：
- summary 必须是50字以内的一句话
- compiled_summary 包含关键数据、数字、方法论
- concepts 是标签数组，代表案例涉及的核心概念/方法论
- entities 是涉及的关键品牌/平台/产品/代理商名称
- tags 是补充性标签如行业、渠道、年度等
- 严格返回JSON，不要加任何解释或markdown格式"""

TARGETS = [
    "SRC-0068", "SRC-0071", "SRC-0075", "SRC-0081", "SRC-0083",
    "SRC-0093", "SRC-0094", "SRC-0095", "SRC-0096", "SRC-0097", "SRC-0098",
]

def call_llm(content: str, src_id: str) -> dict:
    """Call MiniMax LLM to extract compiled_summary."""
    user_prompt = f"来源ID: {src_id}\n\n请分析以下文档内容，提取结构化摘要：\n\n{content[:8000]}"

    payload = {
        "model": MODEL,
        "max_tokens": 1024,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": [{"type": "text", "text": user_prompt}]}],
    }

    req = Request(BASE_URL, data=json.dumps(payload).encode(), headers=HEADERS, method="POST")
    try:
        with urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode())
            text = result["content"][0]["text"].strip()
            # Try to extract JSON from response
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            return json.loads(text.strip())
    except (HTTPError, URLError, json.JSONDecodeError, KeyError) as e:
        print(f"  ❌ LLM API error for {src_id}: {e}")
        # Try to return a minimal result
        return None

def process_source(src_id: str) -> bool:
    manifest_path = MANIFESTS / f"{src_id}.json"
    if not manifest_path.exists():
        print(f"  ❌ {src_id}: manifest not found")
        return False

    with open(manifest_path) as f:
        manifest = json.load(f)

    # Build source file path
    fp = manifest.get("file_path", "")
    if not fp:
        # Try to infer from src_id
        src_file = next(SOURCES.glob(f"*{src_id}.md"), None)
        if not src_file:
            print(f"  ❌ {src_id}: no source file found")
            return False
        fp = src_file.relative_to(KK)

    src_path = KK / fp
    if not src_path.exists():
        print(f"  ❌ {src_id}: source file not found at {src_path}")
        return False

    print(f"  → {src_id}: reading {src_path.name}...")
    content = src_path.read_text(encoding="utf-8", errors="replace")

    result = call_llm(content, src_id)
    if result is None:
        return False

    # Update manifest
    manifest["summary"] = result.get("summary", "")
    manifest["compiled_summary"] = result.get("compiled_summary", "")
    manifest["concepts"] = result.get("concepts", [])
    manifest["entities"] = result.get("entities", [])
    manifest["tags"] = result.get("tags", [])
    manifest["compiled_at"] = "2026-04-15T06:30:00+08:00"

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"  ✅ {src_id}: {manifest.get('title', '?')[:40]}")
    return True

def main():
    print(f"\n📖 Processing {len(TARGETS)} sources...\n")
    success = 0
    for src_id in TARGETS:
        if process_source(src_id):
            success += 1
        else:
            print(f"  ⚠️  Skipping {src_id}")

    print(f"\n✅ Done: {success}/{len(TARGETS)} sources compiled")

    # Run update-index
    import subprocess
    result = subprocess.run(
        ["python3", "/Users/garytan/.openclaw/workspace-dev/skills/knowledge-compiler/scripts/kk_compile.py",
         str(KK), "--update-index"],
        capture_output=True, text=True
    )
    print(result.stdout)
    if result.stderr:
        print(result.stderr)

if __name__ == "__main__":
    main()
