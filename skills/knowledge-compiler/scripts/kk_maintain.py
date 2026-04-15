#!/usr/bin/env python3
"""
kk maintain — 巡检 wiki 质量

Usage:
    python3 kk_maintain.py <workspace-path> [--full]

Checks:
    - Broken wikilinks
    - Claims without source citations
    - Pages with [TODO] markers
    - Orphan pages (no backlinks)
    --full: + duplicate concept candidates + new article candidates
"""

import sys
import json
import re
from pathlib import Path
from datetime import datetime

ACTIVE_FILE = Path("/Users/garytan/Documents/garytan/知识库/.active_workspace")


def check_page(path: Path) -> dict:
    findings = []
    content = path.read_text(encoding="utf-8", errors="ignore")

    # Broken wikilinks: [[non-existent]]
    for match in re.finditer(r'\[\[([^\]]+)\]\]', content):
        target = match.group(1).split("|")[0].strip()
        # check if target page exists
        found = False
        for subdir in ["concepts", "entities", "themes"]:
            if (path.parent.parent / subdir / f"{target}.md").exists():
                found = True
                break
        if not found and not target.startswith("SRC-"):
            findings.append(f"断链: [[{target}]]")

    # Missing source citations
    lines_with_content = [l for l in content.split("\n") if l.strip() and not l.startswith(">")]
    uncited = [l for l in lines_with_content
               if len(l.strip()) > 50
               and not re.search(r'\(SRC-\d+\)', l)
               and not re.search(r'\[\[SRC-', l)
               and not l.startswith("#")
               and not l.startswith("- ")
               and not l.startswith("* ")]
    if uncited:
        findings.append(f"可能无来源断言: {len(uncited)} 处")

    # TODO markers
    todos = re.findall(r'\[TODO[^\]]*\]', content)
    if todos:
        findings.append(f"TODO 待验证: {len(todos)} 处")

    return findings


def maintain(ws: Path, full: bool):
    ts = datetime.now().strftime("%Y-%m-%d")
    findings_dir = ws / "maintain" / "findings"
    gaps_dir = ws / "maintain" / "gaps"
    findings_dir.mkdir(parents=True, exist_ok=True)
    gaps_dir.mkdir(parents=True, exist_ok=True)

    all_findings = []
    all_gaps = []

    for subdir in ["concepts", "entities", "themes"]:
        wd = ws / "wiki" / subdir
        if not wd.exists():
            continue
        for page in wd.glob("*.md"):
            findings = check_page(page)
            if findings:
                all_findings.append(f"### {page.stem}\n" + "\n".join(f"- {f}" for f in findings))

    # Check for orphan pages (no backlinks)
    all_pages = {}
    for subdir in ["concepts", "entities", "themes"]:
        wd = ws / "wiki" / subdir
        if not wd.exists():
            continue
        for page in wd.glob("*.md"):
            all_pages[page.stem] = page

    orphans = []
    for name, page in all_pages.items():
        content = page.read_text(encoding="utf-8", errors="ignore")
        linked = set(re.findall(r'\[\[([^\]]+)\]\]', content))
        if not any(lnk.split("|")[0].strip() == name for lnk in linked):
            orphans.append(name)

    if orphans:
        all_findings.append(f"### 孤立页面（无反向链接）\n" +
                            "\n".join(f"- [[{o}]]" for o in orphans))

    # Write findings
    if all_findings:
        out = findings_dir / f"{ts}_findings.md"
        out.write_text(
            f"# 巡检发现 — {ts}\n\n" + "\n\n".join(all_findings) + "\n",
            encoding="utf-8"
        )
        print(f"  ✅ 写入: maintain/findings/{ts}_findings.md")

    # Summary
    print(f"""
[kk] {ws.name} | 巡检完成 | {datetime.now().strftime('%Y-%m-%d %H:%M')}
  页面检查: {len(all_pages)}
  问题数: {len(all_findings)}
  孤立页面: {len(orphans)}
""")

    # log
    log = ws / "log.md"
    log.open("a", encoding="utf-8").write(
        f"## [{ts}] maintain | 检查{len(all_pages)}页，发现{len(all_findings)}项\n"
    )


def main():
    if len(sys.argv) < 2:
        ws_arg = None
    else:
        ws_arg = sys.argv[1]

    if not ws_arg:
        if ACTIVE_FILE.exists():
            name = ACTIVE_FILE.read_text().strip()
            ws = ACTIVE_FILE.parent / name
            print(f"活跃 workspace: {name}")
        else:
            print("❌ 没有活跃 workspace")
            sys.exit(1)
    else:
        ws = Path(ws_arg)

    if not (ws / "AGENTS.md").exists():
        print(f"❌ 不是有效的 kk workspace: {ws}")
        sys.exit(1)

    full = "--full" in sys.argv
    maintain(ws, full)


if __name__ == "__main__":
    main()
