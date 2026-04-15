#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime

WORKSPACE = Path('/Users/garytan/.openclaw/workspace-dev')
MEMORY = WORKSPACE / 'memory'
ONTOLOGY = MEMORY / 'ontology'
GRAPH = ONTOLOGY / 'graph.jsonl'
SCHEMA = ONTOLOGY / 'schema.yaml'
TODAY = MEMORY / '2026-04-05.md'


def read_jsonl(path: Path):
    rows = []
    for i, line in enumerate(path.read_text().splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        rows.append((i, json.loads(line)))
    return rows


def audit_graph():
    entities = {}
    rels = []
    duplicate_entities = []
    bad_json = []
    for i, obj in read_jsonl(GRAPH):
        if obj.get('op') == 'create':
            ent = obj.get('entity', {})
            eid = ent.get('id')
            if not eid:
                bad_json.append((i, 'create_missing_id'))
                continue
            if eid in entities:
                duplicate_entities.append((i, eid))
            entities[eid] = ent
        elif obj.get('op') == 'relate':
            rels.append((i, obj))
    missing_refs = []
    for i, rel in rels:
        if rel.get('from') not in entities:
            missing_refs.append((i, 'from', rel.get('from'), rel.get('rel'), rel.get('to')))
        if rel.get('to') not in entities:
            missing_refs.append((i, 'to', rel.get('to'), rel.get('rel'), rel.get('from')))
    return {
        'entity_count': len(entities),
        'relation_count': len(rels),
        'duplicate_entities': duplicate_entities[:20],
        'missing_refs': missing_refs[:50],
        'ok': not duplicate_entities and not missing_refs and not bad_json,
    }


def ensure_today_note():
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    block = f"""# 2026-04-05\n\n## {now} 记忆系统巡检\n- 巡检结论：LCM 正常、memory_search 当前可用，但今日日记缺失，ontology 增量落后，task ledger 有 stale running 与时间戳异常。\n- `memory/2026-04-05.md` 此次由巡检补建，避免今天记忆继续断档。\n- `memory/ontology/graph.jsonl` 与 `schema.yaml` 目前仍需专项修复脚本处理，不能假装已补齐。\n- 建议后续动作：\n  1. 清理 stale running tasks\n  2. 修复 ontology schema/graph 增量\n  3. 验证 daily-memory-refresh 恢复\n"""
    if TODAY.exists():
        txt = TODAY.read_text()
        if '记忆系统巡检' not in txt:
            TODAY.write_text(txt.rstrip() + '\n\n' + block.split('\n', 1)[1])
            return 'appended'
        return 'present'
    TODAY.write_text(block)
    return 'created'


def main():
    result = {
        'today_note': ensure_today_note(),
        'graph_audit': audit_graph(),
        'files': {
            'today_note_exists': TODAY.exists(),
            'schema_exists': SCHEMA.exists(),
            'graph_exists': GRAPH.exists(),
        }
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
