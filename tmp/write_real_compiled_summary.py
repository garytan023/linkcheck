#!/usr/bin/env python3
import json

manifest_path = '/Users/garytan/Documents/garytan/宇先生/知识库/karpathy-pkm/manifests/sources/SRC-0082.json'

compiled = {
    "summary": "Swisse 2026年Q1京东付费投放复盘（群邑电商制作）。报告覆盖蓟类提取物、鱼油、增强骨质、维生素、蛋白粉、婴童维矿、DHA七大品类，分为人群资产分析、重点品类情况、店铺付费复盘三大板块。整体结论：品牌A1暴增但A2滞涨（除鱼油外），流量大但转化链路断裂；鱼油是唯一品类内流转健康的品类；蛋白粉量下滑未能跑赢大盘；整体付费ROI 5.7但新客质量存疑。报告数据存在多处前后矛盾：蓟类站外贡献比例说法不一、鱼油老客占比与段落结论相悖、蛋白粉类目新老客加总与整体数字不符。",
    
    "concepts": [
        "4A人群流转模型",
        "A1到A2流转率断崖",
        "品类新客vs纯品类新客定义混用",
        "站内外流量协同",
        "付费ROI与直接ROI的区别",
        "老客复购驱动增长",
        "跨类目人群再营销",
        "竞品拦截策略",
        "内容营销与付费广告协同",
        "货品差异化打法",
        "人群重叠度分析",
        "摇摆客净转化"
    ],
    
    "entities": [
        "Swisse（斯维诗）",
        "京东",
        "群邑电商（GroupM Nexus）",
        "蓟类提取物（护肝）",
        "鱼油",
        "增强骨质",
        "维生素",
        "蛋白粉",
        "婴童维矿",
        "婴童DHA",
        "汤臣倍健",
        "金凯撒",
        "健安喜",
        "钙尔奇"
    ],
    
    "key_findings": [
        "核心矛盾：A1暴增53%但A2仅增2%，A1→A2流转率下滑 — 流量大但转化链路断裂，这是全场最大结构性问题",
        "数据矛盾1：蓟类章节说站外贡献A1的84%，但图表显示站外占比仅26%，前后矛盾",
        "数据矛盾2：鱼油章节段落说「老客暴涨73%」，但SKU表中1500mg老客增长仅39%、高纯鱼油表老客6801%，数据可信度低",
        "数据矛盾3：蛋白粉新老客加总不符（品类新+品类老+品牌品类新≠总数），整体数字自洽性差",
        "Working：鱼油品类 — 站内站外协同好，流转健康，老客基数大且增长稳健（73%+），ROI 5.8，品类天花板高",
        "Working：婴童维矿 — 逆势增长48%，跑赢大盘，老客复购强（+64%），LS系列打法清晰",
        "Working：增强骨质老客 — 老客复购31%，100元以下价格带暴涨279%，承接低价段能力强",
        "Not Working：蓟类站外投放策略 — 去年暂停站外导致成本上升432%，A1靠站外但站外又不能稳",
        "Not Working：蛋白粉品类 — 品牌下滑16%而行业增长13%，份额被伊利等新品牌侵蚀，新客引入失效",
        "Not Working：维生素品类 — 店铺增速16%远低于行业26%，新客被新品牌抢走，品牌定位模糊",
        "Not Working：蓟类素材方向 — 新方向素材点击率低于原投放素材，文案方向失败",
        "Not Working：鱼油高纯方向 — 直接ROI仅1.0（男维D），新客率64%但转化效率差，测试方向不对"
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

print("✅ SRC-0082 compiled_summary updated")
print(f"   Concepts: {len(compiled['concepts'])}")
print(f"   Entities: {len(compiled['entities'])}")
print(f"   Key findings: {len(compiled['key_findings'])}")
