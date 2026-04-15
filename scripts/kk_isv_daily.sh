#!/bin/bash
# karpathy-pkm ISV 目录每日同步脚本
# 功能：监控 /Users/garytan/Documents/garytan/宇先生/Documents/ISV
# 新增 PPTX → 提取文本 → ingest → compiled_summary → build-wiki → update-index

KK="/Users/garytan/Documents/garytan/宇先生/知识库/karpathy-pkm"
ISV_SRC="/Users/garytan/Documents/garytan/宇先生/Documents/ISV"
ISV_RAW="$KK/raw/ISV"
SOURCES="$KK/sources"
SKILL="/Users/garytan/.openclaw/workspace-dev/skills/knowledge-compiler/scripts"
LOG="$HOME/.openclaw/logs/kk_isv_daily.log"

log() { echo "[$(date '+%Y-%m-%d %H:%M')] $*" | tee -a "$LOG"; }

log "=== ISV daily sync 开始 ==="

# 1. 复制新增 PPTX 文件
mkdir -p "$ISV_RAW"
find "$ISV_SRC" -maxdepth 1 -type f ! -name ".DS_Store" ! -name "*textClipping*" | while read f; do
    fname=$(basename "$f")
    if [ ! -f "$ISV_RAW/$fname" ]; then
        cp -v "$f" "$ISV_RAW/" 2>&1 | tee -a "$LOG"
        log "新增文件: $fname"
    fi
done

# 2. 提取新增 PPTX 文本 → .md
python3 << 'PYEOF' >> "$LOG" 2>&1
import json, time, hashlib, sys
from pathlib import Path
from datetime import datetime

KK = Path("$KK")
ISV_RAW = Path("$ISV_RAW")
SOURCES = Path("$SOURCES")
MS = KK / "manifests/sources"

try:
    from pptx import Presentation
except ImportError:
    print("python-pptx 未安装")
    sys.exit(1)

def extract_pptx_text(path):
    prs = Presentation(str(path))
    lines = []
    for i, slide in enumerate(prs.slides, 1):
        lines.append(f"\n## Slide {i}\n")
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip():
                lines.append(shape.text.strip() + "\n")
    return "\n".join(lines)

# 找下一个 SRC ID
existing_ids = []
for mf in MS.glob("SRC-*.json"):
    try:
        n = int(mf.stem.split("-")[1])
        existing_ids.append(n)
    except: pass
next_num = max(existing_ids) + 1 if existing_ids else 1

new_count = 0
for ppx in ISV_RAW.glob("*.pptx"):
    # 检查是否已处理（通过 hash）
    h = hashlib.sha256()
    h.update(ppx.read_bytes())
    content_hash = h.hexdigest()
    
    dup = False
    for mf in MS.glob("SRC-*.json"):
        if json.loads(mf.read_text()).get("content_hash") == content_hash:
            dup = True
            break
    
    if dup:
        print(f"已存在，跳过: {ppx.name}")
        continue
    
    print(f"提取: {ppx.name}")
    text = extract_pptx_text(ppx)
    if len(text.split()) < 20:
        print(f"内容过少 ({len(text)} chars)，跳过")
        continue
    
    src_id = f"SRC-{next_num:04d}"
    next_num += 1
    
    md_name = f"ISV-{ppx.stem}_SRC-{src_id}.md"
    md_path = SOURCES / md_name
    
    h2 = hashlib.sha256()
    h2.update(text.encode("utf-8"))
    chash = h2.hexdigest()
    
    md_content = f"# {ppx.stem}\n\n*来源: {ppx.name}*\n*提取时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n{text}"
    md_path.write_text(md_content, encoding="utf-8")
    
    manifest = {
        "id": src_id,
        "title": ppx.stem,
        "type": "article",
        "source_url": None,
        "date_ingested": datetime.now().strftime("%Y-%m-%d"),
        "date_published": None,
        "file_path": f"sources/{md_name}",
        "content_hash": chash,
        "summary": None,
        "compiled_summary": None,
        "concepts": [],
        "entities": [],
        "tags": ["ISV"],
        "raw_file": str(ppx.relative_to(KK.parent.parent))
    }
    
    with open(MS / f"{src_id}.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    
    print(f"✅ {src_id}: {ppx.name}")
    new_count += 1

print(f"新增 {new_count} 个 source")
PYEOF

log "=== ISV sync 完成 ==="
