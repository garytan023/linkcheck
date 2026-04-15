#!/usr/bin/env python3
import json

manifest_path = '/Users/garytan/Documents/garytan/宇先生/知识库/karpathy-pkm/manifests/sources/SRC-0082.json'

compiled = {
    "summary": "Swisse 2026年Q1京东付费投放复盘报告（群邑电商制作）。核心发现：Q1品牌4A总量2.56亿，同比增长40%，A1增长53%但A2仅增2%，流转率下滑；A3/A4均增20%+，后链路运营效率较高。站内内容同比增长81%是增长主力，站外内容营销新增A1同比增长115%。重点品类情况分析显示高价值用户承接能力待提升。",
    "concepts": [
        "4A人群模型",
        "A1A2A3A4人群分层",
        "站内外流量协同",
        "付费投放复盘",
        "电商营销科学",
        "人群资产运营",
        "内容营销驱动增长",
        "新老客分层运营",
        "后链路转化效率",
        "A1到A2流转率"
    ],
    "entities": [
        "Swisse",
        "京东",
        "群邑电商",
        "A1（认知人群）",
        "A2（吸引人群）",
        "A3（行动人群）",
        "A4（拥护人群）"
    ],
    "key_findings": [
        "A1同比增长53%至19994w，但A2仅增2%，A1→A2流转率下滑，用户承接能力不足",
        "站内内容同比增长81%是站内增长主力，广告（剔除站外）增长37%",
        "站外内容营销新增A1同比增长115%，是站外渠道主要增量来源",
        "A3同比增19%，A4同比增28%，后链路运营效率较高",
        "4A总量2.56亿，整体人群同比增长40%"
    ]
}

with open(manifest_path) as f:
    m = json.load(f)

m['compiled_summary'] = compiled
m['summary'] = compiled['summary']
m['concepts'] = compiled['concepts']
m['entities'] = compiled['entities']
m['key_findings'] = compiled['key_findings']

with open(manifest_path, 'w') as f:
    json.dump(m, f, ensure_ascii=False, indent=2)

print(f"✅ SRC-0082 compiled_summary written")
print(f"   Concepts: {len(compiled['concepts'])}")
print(f"   Entities: {len(compiled['entities'])}")
