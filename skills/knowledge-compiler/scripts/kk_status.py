#!/usr/bin/env python3
"""
kk status — 显示 workspace 状态

Usage:
    python3 kk_status.py <workspace-path>
"""

import sys
import json
import csv
from pathlib import Path


def status(ws_path: Path):
    idx = ws_path / "manifests" / "source_index.csv"
    n_sources = 0
    if idx.exists():
        with open(idx, encoding="utf-8") as f:
            n_sources = sum(1 for _ in f) - 1

    n_uncompiled = 0
    ms_dir = ws_path / "manifests" / "sources"
    if ms_dir.exists():
        for mf in ms_dir.glob("SRC-*.json"):
            with open(mf, encoding="utf-8") as f:
                m = json.load(f)
                if m.get("compiled_summary") is None:
                    n_uncompiled += 1

    n_concepts = len(list((ws_path / "wiki" / "concepts").glob("*.md")))
    n_entities = len(list((ws_path / "wiki" / "entities").glob("*.md")))
    n_themes  = len(list((ws_path / "wiki" / "themes").glob("*.md")))
    n_answers = len(list((ws_path / "outputs" / "answers").glob("*.md")))
    n_reports = len(list((ws_path / "outputs" / "reports").glob("*.md")))
    n_curated = len(list((ws_path / "curated" / "promoted").glob("*.md")))

    print(f"""
[kk] {ws_path.name}
  来源:     {n_sources}
  待编译:   {n_uncompiled}
  wiki:     {n_concepts} 概念 / {n_entities} 实体 / {n_themes} 主题
  outputs:  {n_answers} 回答 / {n_reports} 报告
  curated:  {n_curated} 已晋升
""")


def main():
    if len(sys.argv) < 2:
        print("Usage: kk_status.py <workspace-path>")
        sys.exit(1)
    ws = Path(sys.argv[1])
    if not (ws / "AGENTS.md").exists():
        print(f"❌ 不是有效的 kk workspace: {ws}")
        sys.exit(1)
    status(ws)


if __name__ == "__main__":
    main()
