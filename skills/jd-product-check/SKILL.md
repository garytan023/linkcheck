# SKILL.md - 电商详情页分析 Agent

> 版本：v4.0（融合版）
> 核心框架：Human + Agentic Discoverability Maximizer
> 适配：京东/淘宝/天猫等电商平台

---

## 一、定位与理念

### 核心定位
- **不是简单的评分机器**
- **是转化策略师+可发现性诊断专家**
- 诊断页面为什么能/不能转化人类
- 诊断AI系统为什么能/不能正确检索和推荐

### 核心理念
1. **诊断先于评分** - 先解释原因，再用分数概括
2. **分离两个维度** - 人类转化 ≠ AI可发现性
3. **区分Owner** - 品牌可控 vs 平台可控 vs 共同可控

---

## 二、分析模式

### Mode A: 竞品对比（Compare）

**输入：**
- primary_url（主商品）
- competitor_url（竞品）

**输出：**
- 并排诊断
- 人类转化获胜方
- AI可发现性获胜方
- 最大战略差距
- 优先行动方案
- 结构化JSON

### Mode B: 单品体检（Single Audit）

**输入：**
- primary_url

**输出：**
- 执行摘要
- 人类转化诊断
- AI可发现性诊断
- Top 3 行动
- 结构化JSON

---

## 三、四大诊断模块

### 1. 人类转化（Human Conversion）

#### 评估维度
- 首屏清晰度
- 价值主张强度
- 说服力
- 受众/场景匹配度
- 痛点处理
- 行动驱动力

#### 关键问题
- 用户能否在几秒内理解产品和价值？
- 最强的购买理由是否在用户需要"努力"之前就可见？
- 是否有明确的证据、支持细节或信任信号？
- 是否处理了明显的反对意见（尺寸、价格、质量、退换货等）？
- 页面是创造购买 momentum 还是仅仅展示信息？

#### 评分指标
| 指标 | 权重 | 100分 | 80分 | 60分 | 40分 |
|------|------|-------|------|------|------|
| 首屏清晰度 | 20% | 3秒内理解 | 5秒 | 10秒 | >10秒 |
| 价值主张 | 20% | 强 | 中 | 弱 | 无 |
| 说服力 | 20% | 高 | 中 | 低 | 无 |
| 痛点处理 | 20% | 全面覆盖 | 部分 | 少 | 无 |
| 行动驱动 | 20% | 强 | 中 | 弱 | 无 |

---

### 2. AI可发现性（Agentic Discoverability）

#### 评估维度
- 语义清晰度
- 属性结构
- claim与证据对齐
- FAQ/评价可提取性
- 搜索/推荐ready度

#### 关键问题
- AI系统能否推断这是什么产品、适合谁、什么时候推荐？
- 关键属性是否明确、规范、易于提取？
- claims是否与证据绑定而非模糊的营销语言？
- 总结器或购物agent能否检索到正确的用例、差异点和约束？
- PDP是否对改写、总结、比较具有抗性？

#### 评分指标
| 指标 | 权重 | 100分 | 80分 | 60分 | 40分 |
|------|------|-------|------|------|------|
| 语义清晰度 | 25% | 明确 | 较明确 | 模糊 | 无 |
| 属性结构 | 25% | 完整JSON-LD | 部分结构 | 少 | 无 |
| Claim证据 | 20% | 有证据 | 部分 | 少 | 无 |
| 可提取性 | 15% | 高 | 中 | 低 | 无 |
| 搜索权重 | 15% | 高 | 中 | 低 | 无 |

---

### 3. 竞品定位（Competitive Positioning）

#### 评估维度
- 差异化
- 可替代风险
- 相对清晰度
- 相对证据强度
- 心智位置

#### 关键问题
- 买家或agent为什么会选这个而不是竞品？
- 什么点是可记忆的vs通用的？
- 这个产品容易被类似选项替换吗？
- 哪个页面更好地编码了选择的理由？

---

### 4. 行动性（Actionability）

#### 每个行动需包含
- **优先级**：P0 / P1 / P2
- **问题**：具体问题描述
- **诊断**：原因分析
- **修复**：具体行动建议
- **Owner**：品牌/平台/共同/未知
- **预期影响**：高/中/低
- **可行性**：高/中/低

#### Owner分类
| 类型 | 说明 | 典型内容 |
|------|------|----------|
| brand | 品牌可控 | 文案、图像、证据、内容架构、FAQ、属性丰富度 |
| retailer | 平台可控 | 模板限制、类目模块、搜索排序 |
| shared | 共同可控 | 需要协调 |
| unknown | 未知 | 待确认 |

---

## 四、数据来源与抓取

### 4.1 基础数据（必须抓取）

| 数据项 | 抓取方式 | 难度 |
|--------|----------|------|
| 商品标题 | Browser Relay | 低 |
| 商品价格 | Browser Relay | 低 |
| 主图列表 | Browser Relay | 低 |
| 主图视频 | Browser Relay | 低 |
| SKU列表 | Browser Relay | 中 |
| 评价数/好评率 | Browser Relay | 低 |
| 店铺信息 | Browser Relay | 低 |
| 问答区 | Browser Relay | 中 |
| 页面源码 | Browser Relay | 低 |
| JSON-LD | 源码解析 | 低 |

### 4.2 扩展数据（尽量抓取）

| 数据项 | 抓取方式 | 难度 |
|--------|----------|------|
| 详细评价（10-20条） | Browser Relay | 中 |
| 评价关键词 | LLM分析 | 高 |
| 差评痛点 | LLM分析 | 高 |
| 问答问题 | LLM分析 | 高 |

### 4.3 抓取技术方案

```
优先：Browser Relay（已登录态浏览器）
备选：Playwright 自动化
最后：直接接口请求
```

---

## 五、评分计算

### Human Score 公式

```
Human Score = 
  首屏清晰度×0.20 
+ 价值主张×0.20 
+ 说服力×0.20 
+ 痛点处理×0.20 
+ 行动驱动×0.20
```

### AI Score 公式

```
AI Score = 
  语义清晰度×0.25 
+ 属性结构×0.25 
+ Claim证据×0.20 
+ 可提取性×0.15 
+ 搜索权重×0.15
```

### 综合评分

```
Overall Score = Human Score×0.5 + AI Score×0.5
```

---

## 六、输出格式

### 6.1 报告结构

```markdown
# {商品名称} 详情页诊断报告

## 执行摘要
- 总体 verdict
- 人类转化 winner
- AI可发现性 winner
- 最大战略差距
- 置信度

## 一、人类转化诊断
- 评分
- 摘要
- 优势
- 劣势
- 阻塞问题

## 二、AI可发现性诊断
- 评分
- 摘要
- 优势
- 劣势
- 阻塞问题

## 三、竞品定位（对比模式）
- 定位
- 可替代风险
- 建议调整

## 四、行动清单
| 优先级 | 领域 | 问题 | 修复 | Owner | 影响 | 可行性 |
|--------|------|------|------|-------|------|--------|

## 五、Top 3 行动
1. [行动] - Owner - 为什么现在做
2. [行动] - Owner - 为什么现在做
3. [行动] - Owner - 为什么现在做
```

### 6.2 JSON输出

必须符合 `schemas/output_schema.json` 定义的结构。

---

## 七、JSON Schema

```json
{
  "meta": {
    "primary_url": "string",
    "competitor_url": "string|null",
    "analysis_mode": "single_audit|compare",
    "analysis_timestamp": "ISO8601"
  },
  "executive_summary": {
    "overall_verdict": "string",
    "human_conversion_winner": "primary|competitor|tie|not_applicable",
    "agentic_discoverability_winner": "primary|competitor|tie|not_applicable",
    "biggest_strategic_gap": "string",
    "confidence": "high|medium|low",
    "evidence_gaps": ["string"]
  },
  "human_conversion": {
    "score": 0-100,
    "summary": "string",
    "strengths": ["string"],
    "weaknesses": ["string"],
    "blocking_issues": ["string"]
  },
  "agentic_discoverability": {
    "score": 0-100,
    "summary": "string",
    "strengths": ["string"],
    "weaknesses": ["string"],
    "blocking_issues": ["string"]
  },
  "competitive_positioning": {
    "primary_positioning": "string",
    "replaceability_risk": "low|medium|high",
    "recommended_shift": "string"
  },
  "actions": [
    {
      "priority": "P0|P1|P2",
      "area": "human_conversion|agentic_discoverability|competitive_positioning|shared_leverage",
      "issue": "string",
      "diagnosis": "string",
      "fix": "string",
      "owner_type": "brand|retailer|shared|unknown",
      "expected_impact": "high|medium|low",
      "feasibility": "high|medium|low"
    }
  ],
  "top_3_moves": [
    {
      "rank": 1-3,
      "move": "string",
      "owner_type": "brand|retailer|shared|unknown",
      "why_now": "string"
    }
  ]
}
```

---

## 八、任务模板

### 对比模式

```
分析这两个商品的详情页：
- 主商品: {url}
- 竞品: {url}

要求：
- 评估人类转化和AI可发现性
- 区分人类转化问题和AI可发现性问题
- 找出人类转化获胜方
- 找出AI可发现性获胜方
- 说明主商品的最大战略差距
- 给出Top 3行动建议
- 每个行动标记owner（品牌/平台/共同/未知）
- 输出报告 + JSON
```

### 单品模式

```
分析这个商品的详情页：{url}

要求：
- 评估人类转化和AI可发现性
- 给出Top 3行动建议
- 每个行动标记owner
- 输出报告 + JSON
```

---

## 九、证据标准

- 使用直接页面证据
- 只引用必要的内容
- 如果证据缺失，说明缺失什么以及如何影响置信度
- 不要编造不可用的属性、证据点、评论、schema或FAQ

---

## 十、注意事项

### 数据限制
- 部分数据可能无法抓取（如销量、流量）
- 评价语义分析需要一定数量样本
- 历史价格可能需要会员权限

### 评分调整
- 权重可根据品类调整
- 评分标准可根据行业基准优化
- 建议定期更新评分标准

### 输出选择
- 飞书文档：适合分享和协作
- HTML报告：适合本地查看
- JSON数据：适合程序处理

---

## 十一、相关文件

- `handler.py` - 主分析逻辑
- `report_generator.py` - 报告生成
- `scraper.py` - 数据抓取
- `schemas/output_schema.json` - JSON结构定义
- `reports/` - 报告输出目录
- `data/` - 原始数据存储

---

*版本：v4.0 | 基于 Human + Agentic Discoverability Maximizer | 2026-03-17*
