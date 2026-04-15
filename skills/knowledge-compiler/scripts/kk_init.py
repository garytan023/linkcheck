#!/usr/bin/env python3
"""
kk init — 创建新研究 workspace

Usage:
    python3 kk_init.py <project-name>

Creates:
    <BASE>/<project-name>/
        AGENTS.md
        log.md
        inbox/
        sources/
        manifests/
            sources/
            source_index.csv
        wiki/
            indexes/
                master_index.md
            concepts/
            entities/
            themes/
        outputs/
            answers/
            reports/
        maintain/
            findings/
            gaps/
            candidates/
        curated/
            promoted/
"""

import sys
import csv
from pathlib import Path
from datetime import datetime

BASE_DIR = Path("/Users/garytan/Documents/garytan/知识库")
ACTIVE_FILE = BASE_DIR / ".active_workspace"

DIRS = [
    "inbox",
    "sources",
    "manifests/sources",
    "wiki/indexes",
    "wiki/concepts",
    "wiki/entities",
    "wiki/themes",
    "outputs/answers",
    "outputs/reports",
    "maintain/findings",
    "maintain/gaps",
    "maintain/candidates",
    "curated/promoted",
]


def generate_agents_md(project_name: str) -> str:
    return f"""# {project_name} — 研究 Workspace

> LLM 操作此 workspace 的唯一契约。每次操作前必须读取。

## 项目信息

- **项目名**: {project_name}
- **创建日期**: {datetime.now().strftime('%Y-%m-%d')}
- **来源数**: 0
- **wiki 页数**: 0
- **状态**: 初始化完成，等待 ingest

## 目录契约

| 目录 | 性质 | 说明 |
|------|------|------|
| `log.md` | 时间线 | Append-only 操作日志 |
| `inbox/` | 入口 | 原始来源投入口 |
| `sources/` | 权威 | 已登记来源副本，只读 |
| `manifests/sources/` | 元数据 | 每个来源一个 SRC-NNNN.json |
| `manifests/source_index.csv` | 索引 | 来源汇总 |
| `wiki/` | 派生 | 可从 sources 重建 |
| `outputs/` | 临时 | ask/maintain 产物 |
| `maintain/` | 诊断 | 巡检结果 |
| `curated/promoted/` | 认可 | 最终产物 |

## 硬规则

1. `sources/` 只读，不准直接修改
2. 所有非平凡断言必须可回链到 source manifest
3. 无来源的推测用 `[TODO: 待验证]`
4. `log.md` 是 append-only，不准手动修改

## Source Manifest Schema

```json
{{
  "id": "SRC-NNNN",
  "title": "来源标题",
  "type": "article|paper|book|video|tweet|other",
  "source_url": null,
  "date_ingested": "YYYY-MM-DD",
  "date_published": null,
  "file_path": "sources/filename.md",
  "content_hash": "SHA-256",
  "summary": null,
  "compiled_summary": null,
  "concepts": [],
  "entities": [],
  "tags": []
}}
```
"""


def create_source_index_csv(workspace_path: Path):
    path = workspace_path / "manifests" / "source_index.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "title", "type", "date_ingested", "file_path", "content_hash"])


def init_workspace(project_name: str) -> bool:
    wp = BASE_DIR / project_name

    if wp.exists():
        print(f"❌ 已存在: {wp}")
        return False

    BASE_DIR.mkdir(parents=True, exist_ok=True)

    for d in DIRS:
        (wp / d).mkdir(parents=True, exist_ok=True)

    (wp / "AGENTS.md").write_text(generate_agents_md(project_name), encoding="utf-8")

    create_source_index_csv(wp)

    # master_index
    idx = wp / "wiki" / "indexes" / "master_index.md"
    idx.write_text(f"# {project_name} — Master Index\n\n> 自动生成，勿手动编辑。\n\n## Concepts\n\n_（尚无）_\n\n## Entities\n\n_（尚无）_\n\n## Themes\n\n_（尚无）_\n", encoding="utf-8")

    # log.md
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    (wp / "log.md").write_text(f"## [{ts}] init | 创建 workspace {project_name}\n", encoding="utf-8")

    # active
    ACTIVE_FILE.write_text(project_name, encoding="utf-8")

    print(f"✅ 创建: {wp}")
    print(f"✅ AGENTS.md / log.md / source_index.csv / master_index.md")
    print(f"✅ 设为活跃 workspace: {project_name}")
    print()
    print(f"[kk] {project_name} | 来源: 0 | wiki: 0 页 | 状态: 初始化完成，等待 ingest")
    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: kk_init.py <project-name>")
        sys.exit(1)
    ok = init_workspace(sys.argv[1])
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
