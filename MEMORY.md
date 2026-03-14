# MEMORY.md - 长期记忆

## 拉小风档案
- **名字**: 拉小风（Gary取的）
- **形象**: 可爱白色AI小狗 🐶
- **角色**: 老大，统筹6个拉小兄弟
- **头像**: avatars/xiaola.png

---

## Agent 家族

| # | 角色 | 功能 |
|---|------|------|
| 1️⃣ | 信息知识助理 | 搜索、整理、总结 |
| 2️⃣ | 数据分析师 | 指标、报表、归因 |
| 3️⃣ | 媒介投放助理 | 抖音/小红书/京东投放 |
| 4️⃣ | 创意设计师 | 脚本、素材、落地页 |
| 5️⃣ | 程序员 | 爬虫、自动化、脚本 |

---

## 重要配置
- **12AI API**: https://cdn.12ai.org (sk-8xBdlzdEiSP3QDjKna7fDDMknJ4Bh6YLNUrxFruG7ZPGxszf)
- **飞书App**: cli_a9f1b6fb6b3bdbc2
- **Notion**: 已配置
- **Discord**: 已配置
- **WhatsApp**: 已连接

## Skills
- china-ads-audit（广告审计）
- memory-tiering（三层记忆）
- notion（已配置）
- ddg-web-search, brave-api-search（搜索）
- playwright-scraper-skill（爬虫）

## Gary的偏好
- 拒绝废话和讨好
- 有观点直说
- 中文环境用中文
- 做蠢事会骂
- 重要信息不要只依赖插件记忆，必须落到本地文件
- 先查再问，先验证再汇报

---

### 2026-03-10
- 自动化日报交接给拉小知负责
- 创建文档: memory/自动化日报全流程.md
### 2026-03-10
- 标准化每日资讯同步流程，写入 skill
- 修复RSS解析：用XML解析器，不是正则
- 分类逻辑：关键词分类，不是按公众号
- 日期过滤：只取昨日内容
- 创建 skill: daily-news-sync
- 创建脚本: daily_news_sync_v2.py

### 2026-03-09
- 收藏清华姜学长视频笔记：别再给AI定角色了，这两个方法更有效
- 重新定位：我是老大，统筹5个专业Agent
- 更新 AGENTS.md 和 SOUL.md
- 每天9点自动生成日报（小拉知负责）

### 2026-03-08
- 完成首次公众号资讯精选同步（45个RSS源 → 30条精选）
- 同步到Discord频道 1478997781187268608
- 同步到Notion（每日资讯页面）
- 同步到飞书（新建文档并共享给Gary full_access）
- 飞书文档链接: https://feishu.cn/docx/HIdkdYxdYoc9GTxyXjZcPO33nQg

### 2026-03-10 晚
- 飞书文档写入权限问题解决
- 方案：脚本创建文档 → feishu_doc工具写入内容
- 原因：APP的tenant_access_token没有docx写入权限，但feishu_doc工具有用户授权
- 更新了 SKILL.md 记录完整流程
