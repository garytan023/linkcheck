# 🤖 5 个 Agent 完整配置

## 1️⃣ 信息知识助理（Info / Knowledge）
**模型**：`claude-sonnet-4-6`

| 能力 | Skills |
|------|--------|
| 搜索检索 | `ddg-web-search`, `brave-api-search`, `tavily-search` |
| 总结提炼 | `summarize` |
| 知识库 | `agent-memory` |
| 需求拆解 | 内置能力 |

**运行规则**：先查再说，引用来源，不猜数据

---

## 2️⃣ 数据分析助理（Data / BI）
**模型**：`gpt-4o`

| 能力 | Skills |
|------|--------|
| 数据清洗 | `data-analysis` |
| 指标体系 | `data-analysis` |
| Excel处理 | `microsoft-excel` |
| 电商分析 | `ecommerce-creative-analyst` |

**运行规则**：先确认口径，所有结论可复算

---

## 3️⃣ 媒介投放助理（Media）— ⏸️ 暂留空

---

## 4️⃣ 创意设计助理（Creative）
**模型**：`MiniMax-M2.5`

| 能力 | Skills |
|------|--------|
| 创意策略 | `superpower` |
| 脚本文案 | `superpower` |
| 浏览器调研 | `agent-browser` |
| 网页抓取 | `playwright-scraper-skill` |

---

## 5️⃣ 程序员助理（Engineer）
**模型**：`claude-sonnet-4-6`

| 能力 | Skills |
|------|--------|
| 编程 | `coding` |
| API集成 | `anthropic` |
| 自动化 | `coding` |
| Skill创建 | `skill-creator` |

---

## 📊 当前 Skills 总表

| 分类 | Skills |
|------|--------|
| 搜索/记忆 | `ddg-web-search`, `brave-api-search`, `tavily-search`, `agent-memory`, `summarize` |
| 数据分析 | `data-analysis`, `microsoft-excel`, `ecommerce-creative-analyst` |
| 创意/浏览器 | `superpower`, `skill-creator`, `playwright-scraper-skill`, `agent-browser` |
| 程序员 | `coding`, `anthropic` |
| 工具 | `find-skills`, `openclaw-skill-vetter`, `proactive-agent-skill`, `self-improvement` |
