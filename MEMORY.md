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

---

## 2026-04-24（每日整理）

### Ontology 重大格式修复
- **问题发现**：graph.jsonl 中 993 条旧格式 entries（`{"op": "relate"...}` shorthand，缺少 entity.id）混入 326 条新格式，导致 validator 报 MISSING ID 错误
- **修复**：全部 993 条转换为标准 `{"op": "create", "entity": {"id": ..., "type": "Relation", ...}}` 格式
- **额外修复**：2条 relation reference 错误（`agent_ecom-vision-gemini31` → `agent_ecom_vision_gemini31`）
- **当前 ontology**：**1465 entities** / 0 errors / 0 warnings ✅
  - Session: 321 | Relation: 1066 | SummaryNote: 26 | Agent: 14 | Rule: 9 | Topic: 9 | ...

### Session 注册（幂等）
- 新注册 73 sessions（cron=39, active_work=12, dev=16, assistant=5, creative=1）
- Gary 回归（04-23 22:36），10天沉默打破，主 session 537KB
- RSS 资讯精选改用 interactive card 格式（21个可点击按钮）

---

## 2026-04-24（每周整理）——04-17~04-24

### 本周最大事件
- **Gary 10天沉默打破（04-22~04-23）**：04-22 22:36 主 session 突现6.6MB，涉及抖音618营销图片素材分发；04-23 22:36 Gary 继续活跃（537KB），完成 PPT Slide 10；la_xiao_chuang 同日结束10天休眠，收到 Claude Design 30条准则并生成 WPP 图片

### Ontology 重大进展
- **格式修复（04-24）**：993条旧格式 entries 全部转换为标准 entity.id 格式；2条错误 relation reference 修正；验证：1465 entities / 0 errors / 0 orphans ✅（历史最佳）
- **持续净增**：从 04-16 的 518 entities 增长到 04-24 的 1465 entities（+947，含 session 注册）

### karpathy-pkm / ISV 进展
- **新批次入库（04-17）**：SRC-0102（京东广告产品手册）+ SRC-0103（618大促营销指南）
- **Manifest 编号漂移**：SRC-0097~0103 编号漂移待 Gary 清理
- **Obsidian sync 脚本**：`obsidian_doc_sync_to_kk.py` 打通（raw/obsidian-docs + inbox/obsidian-docs）
- **小红书商业产品全景手册 75页 OCR（04-17）**：Subagent 完成，60KB/1283行文本

### xhs-ad-analyst skill（04-16）
- commit `6df1b9b`：接入飞书 Spreadsheet 数据源（`WeZosdIg4hWvWMt0qj5cBqeUnvb`）+ 6个 sheet ID + 实际基准值（Content Type/CPC/CPUV）

### RSS 代理（间续故障）
- **04-18~04-19**：s.ztso.xyz:11211 全挂，daily news 空转
- **04-20 恢复**：34条精选（1337→48→34）成功推送
- **04-21~04-22 再次空转**：7天去重窗口把孤岛内容误判为重复（非代理问题本身）

### 系统稳定性
- **晨间 cron 全部幂等完成**：无重大故障
- **AI Builders Digest**：持续稳定发送
- **重复 cron 并行**：`memory-weekly-review` vs `weekly-memory-review` 仍未合并
- **Git sync 缺口**：weekly-backup 2.0G tar.gz 未完成 git sync

### 跨账号线索
- **dafeng（04-16~04-17）**：Gary 讨论 Claude Code 桌面端、Levie FDE 观点
- **la_xiao_chuang（04-22）**：结束10天休眠，Claude Design 30条准则整合，WPP 图片产出
- **la_xiao_* 全员**：日记 cron 正常完成，系统自运转健康

### 待闭环问题（截至 04-24）
- 🔴 ISV Topic 库 0319 → 飞书文档（Gary 04-13 需求，已11天）
- 🔴 karpathy-pkm reference compile runner（04-11 起，已13天）
- 🔴 Session entity ID 格式统一（271个 legacy underscore 格式）
- 🔴 Manifest 编号漂移（SRC-0097~0103）
- 🔴 RSS 代理稳定性（s.ztso.xyz:11211 持续 Connection refused）
- 🟡 Power BI 远程访问（需 Gary 开启 Chrome CDP）
- 🟡 重复 cron 并行合并（`memory-weekly-review` vs `weekly-memory-review`）
- 🟡 daily-rollup cron 死锁根因

---

## 每周整理（2026-04-25）

### Ontology 重大修复
- **4个重复 session entity IDs 已清除**：4个 session UUID 在 graph 中存在2~3个副本；删除副本保留最早记录；修复后 1517 entries / 424 domain entities / 1093 relations / 0 duplicates / 0 orphans ✅
- **备份**：`graph.jsonl.bak_04_25` / `.bak_04_25b` / `.bak_04_25c`

### 本周事件（04-19~04-25）
- **Gary 沉默规律**：04-19~04-21（3天）、04-24~04-25（2天）两次沉默；沉默=工作节奏，系统保持自转
- **RSS 代理**：持续7天+全挂（s.ztso.xyz:11211 Connection refused）；必须推动 IT 解决
- **Ontology 验证**：424 entities / 1093 relations / 0 orphans / 0 errors ✅（历史最佳）
- **dafeng**：本周无新会话
- **la_xiao_chuang**：design-standards skill 升入主库

### 待闭环问题（截至 04-25）
- 🔴 ISV Topic 库 0319 → 飞书文档（Gary 04-13 需求，**12天**）
- 🔴 karpathy-pkm reference compile runner（04-11 起，**14天**）
- 🔴 RSS 代理稳定性（s.ztso.xyz:11211 **7天+** 持续 Connection refused）
- 🔴 Manifest 编号漂移（SRC-0097~0103）
- 🟡 Power BI 远程访问（需 Gary 开启 Chrome CDP）
- 🟡 重复 cron 并行合并
- 🟡 daily-rollup cron 死锁根因
- 🟢 4个重复 session entity IDs ✅（04-25 修复）

## 2026-04-26（每周整理）

### 系统稳定性
- **Ontology Dedup 完成**：4个重复 session entity IDs 已修复（04-25）；当前 424 entities / 1093 relations / 0 orphans / 0 duplicates ✅
- **RSS 精选三重故障**：04-25 飞书 token / MiniMax 503 / JSON 序列化三环全崩；数据采集成功但未送达 Gary
- **RSS 代理持续故障**：s.ztso.xyz:11211 已 8天+ Connection refused

### Gary 工作流
- **la_xiao_chuang 恢复产出**：04-22 整合 30条 Claude Design 准则，生成 WPP 图片
- **RSS Feishu card 验证成功**：21个可点击按钮格式用户体验良好
- **Gary 沉默规律确认**：04-19~04/21 和 04/24~04/25 两次沉默；沉默是工作节奏，系统保持自转

### 待闭环（多周积压）
- ISV Topic 库 0319 → 飞书文档（04-13 起，13天）
- karpathy-pkm reference compile runner（04-11 起，15天）
- RSS 精选三重故障隔离（04-25 新增）

## 2026-04-27（每周整理 Week 20）

### Ontology 重大进展
- **1个重复 SummaryNote 已清理（04-27）**：`note_session_la_xiao_chuang_4c4c8e09_6320_4cd3_866c_157c76bda727`（underscore，无 created 时间戳）与 canonical dash 版本重复；删除 underscore 版本；SummaryNote 27→26 ✅；备份：graph.jsonl.bak_04_27_weekly
- **141 条 old-format `relate` 条目仍存在**：04-24 修复 993 条后仍有 141 条；不影响功能，建议下次 ontology 大规模刷新时统一迁移
- **当前状态**：1841 entries / 464 Sessions / 1091 Relations / 26 SummaryNotes / 0 orphans ✅

### Gary 沉默（本周 7 天）
- 04-19~04-21（3天）+ 04-24~04-27（4天）= 本周沉默 7 天
- Gary 沉默是工作节奏已成常态，系统自转完全正常，无需干预

### ISV 入库
- **本周首次完整闭环（04-25）**：SRC-0104/0105 7步全通过（raw→文本提取→Manifest→MiniMax摘要→kk_compile→Feishu DM→isv_last_run）
- SIGKILL 偶发但未阻断本次闭环

### 系统稳定性
- **RSS 代理已死 9天+**：s.ztso.xyz:11211 Connection refused 持续；04-25/04-26 精选均缺口；必须推动 IT 解决
- **RSS 三重故障**：飞书 token + MiniMax 503 + JSON 序列化三环全崩；修复方向：拆分错误处理，任何一步失败只影响自己

### 跨账号（dafeng / la_xiao_*）
- **dafeng 本周 0 新 session**：最后活跃 04-16~04-17
- **la_xiao_* 全员实质沉默**：24个 cron session，全部空内容

### 待闭环（截至 04-27）
- 🔴 ISV Topic 库 0319 → 飞书文档（04-13 起，**~16天**）
- 🔴 karpathy-pkm reference compile runner（04-11 起，**~18天**）
- 🔴 RSS 代理死掉（04-18 起，**9天+**）
- 🔴 RSS 精选三重故障隔离（04-25 新增）
- 🟡 141 条 old-format entries（格式迁移）
- 🟡 重复 cron 并行（memory-weekly vs weekly-memory，12天未合并）
- 🟢 重复 SummaryNote ✅（04-27 修复）

## Promoted From Short-Term Memory (2026-04-27)

<!-- openclaw-memory-promotion:memory:memory/2026-04-19.md:15:15 -->
- **Ontology 质量稳定**：567 entities / 1274 relations / 0 orphans，经过 04-18 周整理后 malform entries 已修复。 [score=0.855 recalls=0 avg=0.620 source=memory/2026-04-19.md:15-15]
<!-- openclaw-memory-promotion:memory:memory/2026-04-19.md:5:5 -->
- 今天是系统低效运转日，RSS 代理（s.ztso.xyz:11211）持续故障导致每日资讯精选空转已至少 2 天。晨间 cron 批次基本正常完成，下午 Gary 主 session 介入评估并推进了 RSS 脚本升级（v3 → v4，AI 批量分类）。Ontology 维持历史高位（567 entities / 1274 relations / 0 orphans）。 [score=0.807 recalls=0 avg=0.620 source=memory/2026-04-19.md:5-5]
<!-- openclaw-memory-promotion:memory:memory/2026-04-19.md:11:11 -->
- **RSS 脚本升级 v4 完成**：评估并创建 `daily_news_sync_v4.py`，从逐条分类改为 12AI API 一次批量处理全部文章，速度和稳定性都有提升。HEARTBEAT.md crontab 路径已更新为 `v4.py`。 [score=0.807 recalls=0 avg=0.620 source=memory/2026-04-19.md:11-11]
<!-- openclaw-memory-promotion:memory:memory/2026-04-19.md:13:13 -->
- **晨间批次全部完成**：ISV 每日入库发现 2 个新文件（京东广告产品手册、618大促营销指南），Weekly memory review 确认 Ontology 历史高位无异常，Obsidian Inbox 整理空。 [score=0.807 recalls=0 avg=0.620 source=memory/2026-04-19.md:13-13]
<!-- openclaw-memory-promotion:memory:memory/2026-04-19.md:21:21 -->
- **RSS 代理持续中断**：s.ztso.xyz:11211 Connection refused，每日资讯精选已空转 2 天，output/ 目录最新 RSS 文件停留在 04-14/04-15，断档 4–5 天。备用代理方案未落地。 [score=0.807 recalls=0 avg=0.620 source=memory/2026-04-19.md:21-21]
<!-- openclaw-memory-promotion:memory:memory/2026-04-19.md:23:23 -->
- **Git sync 中断**：weekly-backup 因 SIGKILL 被中断，2.0G tar.gz 备份文件存在于本地但 git sync 未完成，workspace 无新内容同步。 [score=0.807 recalls=0 avg=0.620 source=memory/2026-04-19.md:23-23]
<!-- openclaw-memory-promotion:memory:memory/2026-04-20.md:4:4 -->
- RSS 每日资讯精选在中断2天后于今日恢复，34条精选（1337条→去重48条→精选34条，≥4分）成功推送至 Gary。全天各 Agent 运行平稳，心跳5次均正常响应，无 git commit，无 workspace 改动。Gary 晚间询问了 xhs-ad-analyst skill 安装情况。 [score=0.807 recalls=0 avg=0.620 source=memory/2026-04-20.md:4-4]
