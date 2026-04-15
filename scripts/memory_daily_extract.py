#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime

DATE = datetime.now().strftime('%Y-%m-%d')
workspace = Path('/Users/garytan/.openclaw/workspace-dev')
memory_file = workspace / 'memory' / f'{DATE}.md'
state_file = workspace / 'state' / 'memory_pipeline_state.json'
output_file = Path('/Users/garytan/Documents/garytan/宇先生/OpenClaw-记忆系统/System') / f'Daily-Extract-{DATE}.md'

def pick_lines(text: str, limit: int = 12):
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    keep = []
    for line in lines:
        if line.startswith('#'):
            continue
        if len(line) < 6:
            continue
        if any(bad in line for bad in ['HEARTBEAT_OK', 'gateway connected', 'Inbox 为空']):
            continue
        keep.append(line)
    return keep[:limit]

raw = memory_file.read_text() if memory_file.exists() else ''
picks = pick_lines(raw)
bullets = '\n'.join([f'- {x}' for x in picks]) if picks else '- 今日尚未提炼出有效摘要'

body = f'''---
title: Daily Extract {DATE}
created: {DATE}
updated: {DATE}
status: generated
---

# Daily Extract {DATE}

## 今日重点
{bullets}

## 来源文件
- `{memory_file}`

## 待补 Topic 判断
- 是否形成新制度
- 是否形成新 SOP
- 是否形成可长期复用知识
'''

output_file.write_text(body)
state = {
    'last_run': datetime.now().isoformat(timespec='seconds'),
    'date': DATE,
    'source_exists': memory_file.exists(),
    'picked_count': len(picks),
    'output_file': str(output_file),
    'mode': 'usable'
}
state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2))
print(json.dumps(state, ensure_ascii=False, indent=2))
