# 🤖 5 个 Agent 配置包总览

```
agents-packs/
├── 01-knowledge/          # 信息知识助理
│   ├── SOUL.md
│   ├── AGENTS.md
│   ├── USER.md
│   ├── skills/
│   ├── workflows/
│   ├── templates/
│   ├── heartbeats/
│   └── memory/
│
├── 02-data/              # 数据分析助理
│   ├── SOUL.md
│   ├── AGENTS.md
│   ├── USER.md
│   ├── skills/
│   ├── workflows/
│   ├── templates/
│   ├── heartbeats/
│   └── memory/
│
├── 03-media/             # 媒介投放助理（占位）
│   ├── SOUL.md
│   ├── AGENTS.md
│   ├── USER.md
│   ├── skills/           # 待补充
│   ├── workflows/
│   ├── templates/
│   ├── heartbeats/
│   └── memory/
│
├── 04-creative/          # 创意设计助理
│   ├── SOUL.md
│   ├── AGENTS.md
│   ├── USER.md
│   ├── skills/
│   ├── workflows/
│   ├── templates/
│   ├── heartbeats/
│   └── memory/
│
└── 05-dev/              # 程序员助理
    ├── SOUL.md
    ├── AGENTS.md
    ├── USER.md
    ├── skills/
    ├── workflows/
    ├── templates/
    ├── heartbeats/
    └── memory/
```

## 当前 Skills 分布

| Agent | Skills |
|-------|--------|
| 01-knowledge | ddg-web-search, brave-api-search, tavily-search, agent-memory, summarize |
| 02-data | data-analysis, microsoft-excel, ecommerce-creative-analyst |
| 03-media | （待补充） |
| 04-creative | superpower, agent-browser, playwright-scraper-skill |
| 05-dev | coding, anthropic, skill-creator |

## 模型配置

| Agent | 推荐模型 |
|-------|----------|
| 01-knowledge | claude-sonnet-4-6 |
| 02-data | gpt-4o |
| 03-media | MiniMax-M2.5（暂留空） |
| 04-creative | MiniMax-M2.5 |
| 05-dev | claude-sonnet-4-6 |
