#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime

workspace = Path('/Users/garytan/.openclaw')
public_skills = workspace / 'workspace-dev' / 'skills'
overlay_skills = workspace / 'workspace-dev' / '.agents' / 'skills'
agent_roots = sorted((workspace / 'workspaces').glob('la_xiao_*'))
state_dir = workspace / 'workspace-dev' / 'state'
output = state_dir / 'weekly_skill_memory_audit.json'
ledger = state_dir / 'skill_master_ledger.json'
md_output = Path('/Users/garytan/Documents/garytan/宇先生/OpenClaw-记忆系统/System') / 'Weekly-Skill-Memory-Audit.md'
ledger_md = Path('/Users/garytan/Documents/garytan/宇先生/OpenClaw-记忆系统/System') / 'Skill-Master-Ledger.md'

def dirs(path: Path):
    if not path.exists():
        return []
    return sorted([p.name for p in path.iterdir() if p.is_dir()])

public = set(dirs(public_skills))
overlay = set(dirs(overlay_skills))
all_agent_items = {}
for root in agent_roots:
    all_agent_items[root.name] = set(dirs(root / 'skills'))

agents = {}
for name, items in all_agent_items.items():
    agents[name] = {
        'count': len(items),
        'missing_vs_public': sorted(list(public - items))[:20],
        'extra_vs_public': sorted(list(items - public))
    }

skill_names = sorted(public | overlay | set().union(*all_agent_items.values()) if all_agent_items else public | overlay)
master = []
for skill in skill_names:
    row = {
        'name': skill,
        'in_public': skill in public,
        'in_overlay': skill in overlay,
        'agents': sorted([name for name, items in all_agent_items.items() if skill in items]),
        'layer_judgement': 'public' if skill in public else ('overlay-only' if skill in overlay else 'agent-private'),
        'needs_attention': skill in (overlay - public) or any(skill not in items for items in all_agent_items.values()) if skill in public else True
    }
    master.append(row)

report = {
    'generated_at': datetime.now().isoformat(timespec='seconds'),
    'public_skill_count': len(public),
    'overlay_skill_count': len(overlay),
    'overlay_only': sorted(list(overlay - public)),
    'public_only_count': len(public - overlay),
    'agents': agents
}
output.write_text(json.dumps(report, ensure_ascii=False, indent=2))
ledger.write_text(json.dumps(master, ensure_ascii=False, indent=2))

lines = [
    '# Weekly Skill Memory Audit',
    '',
    f'- generated_at: {report["generated_at"]}',
    f'- public_skill_count: {report["public_skill_count"]}',
    f'- overlay_skill_count: {report["overlay_skill_count"]}',
    f'- overlay_only: {", ".join(report["overlay_only"]) if report["overlay_only"] else "none"}',
    ''
]
for name, data in agents.items():
    lines.append(f'## {name}')
    lines.append(f'- count: {data["count"]}')
    lines.append(f'- extra_vs_public: {", ".join(data["extra_vs_public"]) if data["extra_vs_public"] else "none"}')
    lines.append(f'- missing_vs_public(sample): {", ".join(data["missing_vs_public"]) if data["missing_vs_public"] else "none"}')
    lines.append('')
md_output.write_text('\n'.join(lines))

ledger_lines = ['# Skill Master Ledger', '']
for row in master:
    ledger_lines.append(f'## {row["name"]}')
    ledger_lines.append(f'- layer_judgement: {row["layer_judgement"]}')
    ledger_lines.append(f'- in_public: {row["in_public"]}')
    ledger_lines.append(f'- in_overlay: {row["in_overlay"]}')
    ledger_lines.append(f'- agents: {", ".join(row["agents"]) if row["agents"] else "none"}')
    ledger_lines.append(f'- needs_attention: {row["needs_attention"]}')
    ledger_lines.append('')
ledger_md.write_text('\n'.join(ledger_lines))

print(json.dumps({
    'report': str(output),
    'ledger': str(ledger),
    'overlay_only': sorted(list(overlay - public)),
    'master_count': len(master)
}, ensure_ascii=False, indent=2))
