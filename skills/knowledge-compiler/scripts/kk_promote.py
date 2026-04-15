#!/usr/bin/env python3
"""
kk promote — 晋升产物到 curated/

Usage:
    python3 kk_promote.py <workspace-path> <artifact-path>
"""

import sys
import shutil
from pathlib import Path
from datetime import datetime

ACTIVE_FILE = Path("/Users/garytan/Documents/garytan/知识库/.active_workspace")


def promote(ws: Path, artifact_path: Path) -> bool:
    if not artifact_path.exists():
        print(f"❌ 文件不存在: {artifact_path}")
        return False

    dest_dir = ws / "curated" / "promoted"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / artifact_path.name

    if dest.exists():
        stem = artifact_path.stem
        dest = dest_dir / f"{stem}_{datetime.now().strftime('%Y%m%d%H%M%S')}{artifact_path.suffix}"

    shutil.copy2(artifact_path, dest)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    log = ws / "log.md"
    log.open("a", encoding="utf-8").write(
        f"## [{ts}] promote | {artifact_path.name} → curated/promoted/\n"
    )
    print(f"  ✅ → curated/promoted/{dest.name}")
    print(f"\n晋升完成。如需进一步推到 Obsidian 主库，手动复制文件到目标目录。")
    return True


def main():
    if len(sys.argv) < 3:
        print("Usage: kk_promote.py <workspace-path> <artifact-path>")
        sys.exit(1)

    ws = Path(sys.argv[1])
    if not (ws / "AGENTS.md").exists():
        print(f"❌ 不是有效的 kk workspace: {ws}")
        sys.exit(1)

    artifact = Path(sys.argv[2])
    ok = promote(ws, artifact)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
