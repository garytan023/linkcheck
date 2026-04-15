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
- obsidian-cli（v1.12.7，vault=/Users/garytan/Documents/garytan）
- xiaohongshu-video-to-markdown（视频→markdown pipeline）

## 重要项目状态（截至 2026-04-08）

### karpathy-pkm 知识库
- 状态：**已重建完成**（2026-04-07）
- 内容：37 sources，215 concept pages，Jerman 批次200个概念页修复完毕
- ISV 目录（`/Users/garytan/Documents/garytan/宇先生/Documents/ISV`）**尚未入库**，需继续 ingest 流程

### 小红书视频处理链路
- 元数据：MCP/agent-reach
- 下载：yt-dlp（不用 xiaohongshu-mcp）
- 转写：whisper.cpp + ggml 模型

### karpathy-pkm ISV 目录
- 路径：`/Users/garytan/Documents/garytan/宇先生/Documents/ISV`
- 状态：**未入库**（Gary 确认需求，待处理）

## Gary的偏好（最新）
- 拒绝废话和讨好，有观点直说
- 中文环境用中文，做蠢事会骂
- 重要信息必须落到本地文件，不能只依赖插件记忆
- 先查再问，先验证再汇报
- **【04-03 新增】Gary 直接消息 → 简短"ok"即可，不需要展开解释**

---

### 2026-04-08
- 周整理：更新 HOT/WARM/MEMORY 三层记忆
- karpathy-pkm 重建完成（37 sources，215 concept pages）
- ISV 目录未入库（阻塞 Gary 需求）
- daily-rollup cron 死锁问题记录

### 2026-04-07
- karpathy-pkm workspace 全面重建（Jerman 批次200个概念页修复）
- Gary 询问 ISV 目录入库情况（路径确认：~/宇先生/Documents/ISV）
- RSS 代理全挂（45/45 failed）

### 2026-04-06
- 确认小红书视频处理链路：MCP/agent-reach（metadata）→ yt-dlp（下载）→ ffmpeg（音频）→ whisper.cpp（转写）

### 2026-04-04
- exec 权限恢复（allowlist miss 修复）
- Obsidian CLI 打通（v1.12.7，vault=/Users/garytan/Documents/garytan）
- MiniMax isolated session 模型问题确认：MiniMax-M2.7-highspeed 不支持 tool calls
- 修复方案：5个 isolated agent 改为 MiniMax-Text-01

### 2026-04-03
- Gary 明确要求：直接说"ok"即可，不需要额外文字
- exec.ask 配置受保护字段，无法在线修改，需手动编辑配置文件
- WhatsApp gateway 短暂断连（已知/不紧急）

### 2026-04-02
- 灾难日：8/9 cron 失败（isolated session token plan not supported）
- 主会话消息重复堆积（300+ 重复消息）
- 唯一跑通的 cron：AI Builders Daily Digest（08:30，main session）

### 2026-03-31
- 拉小创（la_xiao_chuang）正式上线，创意设计师角色
- Obsidian CLI skill 开始安装
- skills 同步验证：workspace-dev/skills 为主公共库（51个）

### 2026-03-10
- 自动化日报交接给拉小知负责；创建文档: memory/自动化日报全流程.md
- 标准化每日资讯同步流程，写入 skill；修复RSS解析（XML解析器非正则）、关键词分类、日期过滤
- 创建 skill: daily-news-sync；创建脚本: daily_news_sync_v2.py
- 晚：飞书文档写入权限问题解决（APP tenant_access_token 无写入权，feishu_doc 工具用户授权绕过）

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


---

## 2026-04-11（每周整理）

### 系统稳定性
- **AI Builders Digest 重复触发**：cron 调度器短时间多次触发同一 job，04-09/04-10 均出现；根因未解
- **Session entity paired design 确认**：`session_assistant_XXX` + `note_session_assistant_XXX` 是正常的 session+summary 配对，非重复
- **project_karpathy_pkm entity ID 确认**：正确 ID 为 `project_karpathy_pkm`（非 `proj_karpathy_pkm`）；relation merge 前必须先验证目标 entity 存在

### karpathy-pkm 项目状态
- SRC-0082（Swisse Q1 JD）已入库；82 manifests/215 concept pages
- ISV 目录其余文件待继续 ingest

### Swisse Q1 工作流跑通
- Gary 发图→飞书文档→评论通知→Obsidian 补档，完整链路 04-09 晚验证通过

---

## 2026-04-12（每周整理）

### Ontology 一致性修复（重大）
- **清理18个脏条目**：17个 phantom `session_sessions_*` entries（来自 memory-daily-cleanup cron 错误 agent_id）+ 1个重复 SummaryNote
- **移除17条孤儿关系**：所有 has_session 关系从指向不存在的 `agent_sessions` entity 全部清除
- **清理后**：253 entities / 900 relations / 0 orphans（04-12 验证通过）
- **根因**：`agent_sessions` 是 phantom agent（不存在于配置），session 注册时错误读取了该 ID；教训：session 注册前必须验证 agent_id 真实存在

### karpathy-pkm 项目状态
- SRC-0082（Swisse Q1 JD）已入库；82 manifests/215 concept pages
- ISV 目录其余文件待继续 ingest

### Swisse Q1 工作流（04-10 凌晨追加）
- Gary 发来 CBEC 自营/大贸自营三级类目数据（04-10 00:00 左右）
- 小拉追加第六章（跨境自营+大贸自营各21+24个三级类目Q1同比）
- **⚠️ 数据口径差异**：肠胃益生菌小计与上级汇总不符；Present 前需 Gary 提供原始 Excel 核对
- CBEC自营小结：79.9M → 80.5M（-1%）；大贸自营小结：86.3M → 102.7M（+19%）

### 系统稳定性
- current session cron 机制持续稳定（04-10 晨间验证）；isolated session cron 全灭问题未再触发
- memory-daily-cleanup cron 引入 phantom session 注册 bug（已修复，下次运行可能再次引入，需监控）

---

## 2026-04-13（每周整理）

### Ontology 一致性修复（本次最大事件）
- **清理20个 phantom session entity**（同一 UUID 的 dash vs underscore 格式重复注册）
  - Dash 格式（`session_assistant_xxx-xxx...`）= canonical（对应真实 session 文件名）
  - Underscore 格式（`session_assistant_xxx_xxx...`）= phantom（历史遗留 bug）
  - 删除 20条 phantom entity creates；redirect 79条 phantom relations 到 canonical entity
- **清理后**：270 entities / 937 relations / **0 orphans** ✅（04-13 验证通过）
- Entity breakdown: Session(192) + SummaryNote(26) + Agent(14) + Rule(9) + Topic(9) + ...

### 系统稳定性
- current session cron 机制04-10~04-13持续稳定；isolated session 网络故障未再触发
- AI Builders Digest 幂等 guard 已在 payload 中实施（04-11 方案落地）；但 cron 仍用 isolated session，存在晨间网络故障风险
- ISV每日入库 cron（isolated session）持续 timeout（5次consecutive errors）；已有 current session 版本（ISV Daily Sync to karpathy-pkm）正常工作，建议禁用/删除 isolated 版本

### 跨账号（dafeng）观察
- 04-10 dafeng 线处理 Gary Swisse Q1 需求；dafeng openid: ou_2b61cfc2e4c54c32e1734a48458b1d76
- Gary 关注 AI 动态：Sam Altman $100 Pro 档、levie 非结构化数据观点

### 待闭环问题
- ISV 目录剩余文件 ingest（路径编码问题阻塞）
- 小风/小诊每日日记 cron 持续 timeout（8次/5次consecutive errors）
- AI Builders Digest 应改为 current session
