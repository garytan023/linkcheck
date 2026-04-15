#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
from datetime import datetime

registry = Path('/Users/garytan/.openclaw/workspace-dev/state/skill_registry.json')
registry.parent.mkdir(parents=True, exist_ok=True)

name = sys.argv[1] if len(sys.argv) > 1 else 'UNKNOWN_SKILL'
layer = sys.argv[2] if len(sys.argv) > 2 else 'overlay'
status = sys.argv[3] if len(sys.argv) > 3 else 'testing'
risk = sys.argv[4] if len(sys.argv) > 4 else 'unknown'

items = []
if registry.exists():
    try:
        items = json.loads(registry.read_text())
    except Exception:
        items = []

row = {
    'name': name,
    'layer': layer,
    'status': status,
    'risk': risk,
    'recorded_at': datetime.now().isoformat(timespec='seconds')
}
items.append(row)
registry.write_text(json.dumps(items, ensure_ascii=False, indent=2))
print(json.dumps(row, ensure_ascii=False, indent=2))
