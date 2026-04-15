#!/usr/bin/env python3
"""
kk compile — 增量编译 wiki

Usage:
    python3 kk_compile.py <workspace-path> [--full]

Workflow:
    1. 列出待编译来源（compiled_summary == null）
    2. LLM 读取每个来源，提取 compiled_summary JSON
    3. LLM 调用 --write-summary SRC-NNNN '<json>' 写入 manifest
    4. LLM 调用 --build-wiki 生成 wiki 页面
    5. LLM 调用 --update-index 更新 master_index.md
"""

import sys
import json
import csv
from pathlib import Path
from datetime import datetime

ACTIVE_FILE = Path("/Users/garytan/Documents/garytan/知识库/.active_workspace")


def get_uncompiled(ws: Path):
    results = []
    for mf in sorted((ws / "manifests" / "sources").glob("SRC-*.json")):
        with open(mf, encoding="utf-8") as f:
            m = json.load(f)
        if m.get("compiled_summary") is None:
            results.append(m)
    return results


def get_all_compiled(ws: Path):
    results = []
    for mf in sorted((ws / "manifests" / "sources").glob("SRC-*.json")):
        with open(mf, encoding="utf-8") as f:
            m = json.load(f)
        if m.get("compiled_summary") is not None:
            results.append(m)
    return results


def write_summary(ws: Path, src_id: str, compiled: dict):
    mf_path = ws / "manifests" / "sources" / f"{src_id}.json"
    with open(mf_path, encoding="utf-8") as f:
        m = json.load(f)
    m["compiled_summary"] = compiled
    m["concepts"] = compiled.get("concepts", [])
    m["entities"] = compiled.get("entities", [])
    if compiled.get("summary"):
        m["summary"] = compiled["summary"]
    with open(mf_path, "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=2)
    print(f"  ✅ {src_id}: compiled_summary 已写入")


def write_wiki_page(ws: Path, subdir: str, filename: str, content: str):
    p = ws / "wiki" / subdir / filename
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    print(f"  ✅ wiki/{subdir}/{filename}")


def update_master_index(ws: Path):
    compiled = get_all_compiled(ws)

    concepts = sorted(set(
        c for m in compiled
        for c in m.get("concepts", [])
    ))
    entities = sorted(set(
        e for m in compiled
        for e in m.get("entities", [])
    ))

    concept_lines = "\n".join(f"- [[{c}]]" for c in concepts) or "_（尚无）_"
    entity_lines = "\n".join(f"- [[{e}]]" for e in entities) or "_（尚无）_"

    idx = ws / "wiki" / "indexes" / "master_index.md"
    idx.write_text(f"# {ws.name} — Master Index\n\n"
                    f"> 自动生成，最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                    f"## Concepts\n\n{concept_lines}\n\n## Entities\n\n{entity_lines}\n",
                    encoding="utf-8")
    print(f"  ✅ master_index.md 已更新")


def main():
    ws_arg = sys.argv[1] if len(sys.argv) >= 2 else None

    # 无参数：读 active workspace
    if not ws_arg:
        if ACTIVE_FILE.exists():
            name = ACTIVE_FILE.read_text().strip()
            ws = ACTIVE_FILE.parent / name
            print(f"活跃 workspace: {name}")
        else:
            print("❌ 没有活跃 workspace，先运行: kk init <name>")
            sys.exit(1)
    else:
        ws = Path(ws_arg)

    if not (ws / "AGENTS.md").exists():
        print(f"❌ 不是有效的 kk workspace: {ws}")
        sys.exit(1)

    full = "--full" in sys.argv

    if "--write-summary" in sys.argv:
        # 由 LLM 调用，写入 compiled_summary
        idx = sys.argv.index("--write-summary")
        src_id = sys.argv[idx + 1]
        json_str = sys.argv[idx + 2]
        compiled = json.loads(json_str)
        write_summary(ws, src_id, compiled)
        sys.exit(0)

    if "--write-page" in sys.argv:
        idx = sys.argv.index("--write-page")
        subdir = sys.argv[idx + 1]
        filename = sys.argv[idx + 2]
        content = sys.argv[idx + 3] if len(sys.argv) > idx + 3 else ""
        write_wiki_page(ws, subdir, filename, content)
        sys.exit(0)

    if "--update-index" in sys.argv:
        update_master_index(ws)
        sys.exit(0)

    if "--build-wiki" in sys.argv:
        # 显示 cross-source wiki 生成计划
        compiled = get_all_compiled(ws)
        print(f"\n📚 Cross-source pass: {len(compiled)} 个已编译来源")
        concepts = sorted(set(c for m in compiled for c in m.get("concepts", [])))
        entities = sorted(set(e for m in compiled for e in m.get("entities", [])))
        print(f"  概念: {len(concepts)} 个")
        print(f"  实体: {len(entities)} 个")
        print("\n下一步: LLM 读取所有 compiled_summary，生成/更新 wiki 页面")
        sys.exit(0)

    # 默认：列出待编译来源
    uncompiled = get_uncompiled(ws)
    print(f"\n📖 Per-source pass: {len(uncompiled)} 个待编译来源\n")
    for m in uncompiled:
        print(f"  {m['id']}: {m['title']}")
    print("\n下一步: LLM 逐个读取每个来源文件 → 提取 compiled_summary")
    print("完成后: python3 kk_compile.py <ws> --build-wiki")


if __name__ == "__main__":
    main()
