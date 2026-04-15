from pathlib import Path
import json, csv, shutil, hashlib
from datetime import datetime

ws = Path('/Users/garytan/Documents/garytan/宇先生/知识库/karpathy-pkm')
docs_root = Path('/Users/garytan/Documents/garytan/宇先生/Documents')
text_root = Path('/Users/garytan/.openclaw/workspace-dev/tmp/isv_pdf_text')
manifest_dir = ws / 'manifests' / 'sources'
source_index = ws / 'manifests' / 'source_index.csv'
raw_root = ws / 'raw'
sources_root = ws / 'sources'

entries = [
    {
        'rel': '京东/2026京东全域通招商方案(1).pdf',
        'src_id': 'SRC-0090',
        'source_md': '京东-2026京东全域通招商方案(1)_SRC-0090.md',
        'title': '2026京东全域通招商方案(1)',
        'summary': '京东全域通招商方案，主打一站式全域媒体整合、京东人群深度触达与全链路效果评估。',
        'concepts': ['京东全域通', '全域媒体整合', '联合频控', 'A0-A4人群运营', '全链路效果评估'],
        'entities': ['京东', '京东数坊', 'DMP'],
        'key_findings': [
            '方案强调用京东一方人群和媒介采买能力做跨平台联投，突出高TA浓度和流量保障。',
            '核心卖点是开屏等稀缺资源保价保量，以及大促前预占流量。',
            '评估链路覆盖浏览、关注、加购、购买，兼顾品牌心智和销售转化。'
        ]
    },
    {
        'rel': '京东/WPP-QQ星液体钙新品电商全渠道营销方案 AI定制版.pdf',
        'src_id': 'SRC-0091',
        'source_md': '京东-WPP-QQ星液体钙新品电商全渠道营销方案 AI定制版_SRC-0091.md',
        'title': 'WPP-QQ星液体钙新品电商全渠道营销方案 AI定制版',
        'summary': 'QQ星液体钙新品全渠道营销方案，围绕京东转化、小红书与抖音种草、618跨界联名构建全年增长路径。',
        'concepts': ['新品上市策略', '人群包投放', '内容种草', '618跨界联名', '京东转化闭环'],
        'entities': ['QQ星', '伊利', '京东', '小红书', '抖音', '安踏儿童', '泡泡玛特', '乐高'],
        'key_findings': [
            '战略定位是让QQ星液体钙成为城市家长补钙首选，京东是核心转化阵地。',
            '通过成分党妈妈和身高焦虑型家长两类核心人群，结合搜索推送与PLUS会员权益打透高净值客群。',
            '用小红书科普和抖音专家短视频做心智教育，再借618跨界合作放大声量与转化。'
        ]
    },
    {
        'rel': '阿里/阿里妈妈618营销一站式指南.pdf',
        'src_id': 'SRC-0099',
        'source_md': '阿里-阿里妈妈618营销一站式指南_SRC-0099.md',
        'title': '阿里妈妈618营销一站式指南',
        'summary': '阿里妈妈618营销一站式指南，系统梳理趋势洞察、品牌与效果产品、营销IP资源和经营工具。',
        'concepts': ['618经营策略', '品牌产品矩阵', '效果产品资源', '营销IP', 'AI人群与AIGC'],
        'entities': ['阿里妈妈', '天猫', '淘宝直播', '达摩盘', '88VIP'],
        'key_findings': [
            '手册按趋势洞察、经营策略、产品资源、营销IP和生意工具五大模块组织，适合做618操盘总览。',
            '品牌侧覆盖全域品牌新力、超级新品、品牌特秀、会员日等资源，效果侧覆盖UD效果、人群推广、关键词推广等。',
            '内容和AI能力被放在重要位置，包括AI智能矩阵、AI人群、AIGC、短直联动和淘宝内容场产品。'
        ]
    }
]

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

for e in entries:
    src = docs_root / e['rel']
    raw_dest = raw_root / e['rel']
    raw_dest.parent.mkdir(parents=True, exist_ok=True)
    if not raw_dest.exists():
        shutil.copy2(src, raw_dest)

    txt_path = text_root / (src.stem + '.txt')
    extracted = txt_path.read_text(encoding='utf-8', errors='ignore').strip() if txt_path.exists() else ''
    md_body = f"# {e['title']}\n\n> raw_file: {raw_dest}\n> source_file: {src}\n> date_ingested: 2026-04-15\n\n## 摘要\n\n{e['summary']}\n\n## 提取文本\n\n```text\n{extracted[:120000]}\n```\n"
    md_path = sources_root / e['source_md']
    md_path.write_text(md_body, encoding='utf-8')

    compiled = {
        'summary': e['summary'],
        'concepts': e['concepts'],
        'entities': e['entities'],
        'key_findings': e['key_findings']
    }

    mf_path = manifest_dir / f"{e['src_id']}.json"
    if mf_path.exists():
        m = json.loads(mf_path.read_text(encoding='utf-8'))
    else:
        m = {
            'id': e['src_id'],
            'title': e['title'],
            'type': 'article',
            'source_url': None,
            'date_ingested': '2026-04-15',
            'date_published': None,
            'tags': []
        }
    m.update({
        'title': e['title'],
        'file_path': f'sources/{e["source_md"]}',
        'content_hash': sha256(src),
        'summary': e['summary'],
        'compiled_summary': compiled,
        'concepts': e['concepts'],
        'entities': e['entities'],
        'key_findings': e['key_findings'],
        'raw_file': f'知识库/karpathy-pkm/raw/{e["rel"]}'
    })
    if 'tags' not in m or not isinstance(m['tags'], list):
        m['tags'] = []
    mf_path.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding='utf-8')

rows = []
if source_index.exists():
    with open(source_index, encoding='utf-8', newline='') as f:
        rows = list(csv.reader(f))
ids = {r[0] for r in rows if r}
if 'SRC-0099' not in ids:
    with open(source_index, 'a', encoding='utf-8', newline='') as f:
        csv.writer(f).writerow([
            'SRC-0099',
            '阿里妈妈618营销一站式指南',
            'article',
            '2026-04-15',
            'sources/阿里-阿里妈妈618营销一站式指南_SRC-0099.md',
            sha256(docs_root / '阿里/阿里妈妈618营销一站式指南.pdf')
        ])

log = ws / 'log.md'
ts = datetime.now().strftime('%Y-%m-%d %H:%M')
log.open('a', encoding='utf-8').write(f"## [{ts}] ingest | 3个来源\n- 京东/2026京东全域通招商方案(1).pdf\n- 京东/WPP-QQ星液体钙新品电商全渠道营销方案 AI定制版.pdf\n- 阿里/阿里妈妈618营销一站式指南.pdf\n")

print('updated manifests and sources for 3 files')
