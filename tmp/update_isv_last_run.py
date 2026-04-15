from pathlib import Path
import json
from datetime import datetime, timezone, timedelta

root = Path('/Users/garytan/Documents/garytan/宇先生/Documents')
out = Path('/Users/garytan/.openclaw/workspace-dev/tmp/isv_last_run.json')
snapshot = {}
for f in sorted(root.rglob('*')):
    if f.is_file() and f.suffix.lower() in {'.pdf', '.pptx'}:
        rel = f.relative_to(root)
        folder = rel.parts[0] if len(rel.parts) > 1 else 'ROOT'
        snapshot.setdefault(folder, {})[f.name] = int(f.stat().st_mtime)
now = datetime.now(timezone(timedelta(hours=8))).isoformat()
data = {
    'last_run': now,
    'files_snapshot': snapshot,
    'note': 'Processed 3 new files on 2026-04-15: 京东/2026京东全域通招商方案(1).pdf, 京东/WPP-QQ星液体钙新品电商全渠道营销方案 AI定制版.pdf, 阿里/阿里妈妈618营销一站式指南.pdf'
}
out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
print(out)
