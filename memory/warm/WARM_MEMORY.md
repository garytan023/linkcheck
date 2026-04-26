# WARM Memory - 用户偏好与稳定规则

**最后更新**: 2026-04-25 21:20（每周整理）

## Gary 特点
- 拒绝废话和讨好
- 有观点直说
- 做蠢事会被骂
- 中文环境默认中文
- 更在乎解决问题,不在乎形式好看
- **【2026-04-03 新增】Gary 明确要求:直接说"ok"即可,不需要额外文字** - 收到 Gary 直接消息时,优先简短确认,不需要展开解释或重复信息

## 沟通规则
- 直接回答,别先铺垫
- 不确定就说不确定,不要脑补
- 能自己查清楚的先查,不要反问
- 对外动作要谨慎;对内排查、读文件、整理信息可以主动

## 记忆规则(关键)
- 关键偏好、长期项目、工作流、重要决定必须落盘到本地文件
- 不能只依赖 memory plugin / 向量检索
- plugin 失效时,降级顺序:本地记忆文件 → LCM → 当前上下文
- 每次重要任务完成后,至少更新 HOT/WARM/MEMORY 中一个相关文件

## 技术结论更新(2026-04-14)

### AI Builders Digest 幂等 guard ✅
- daily-rollups/2026-04-13.md 成功生成(22:50 CST);幂等 guard 确认有效,重复触发时跳过发送

### follow-builders git-sync 处理
- `state-feed.json` 本地修改 → git stash → pull → 恢复(Fast-forward);generatedAt: 2026-04-12T07:10:52.880Z

## 当前已知记忆问题
- memory_search 曾出现 embedding provider 401 / invalid_api_key,导致语义召回失效
- lossless-claw 负责压缩上下文,不等于稳定长期记忆
- 三层记忆文件存在,但如果不主动维护,也一样会"形式上有记忆,实际上失忆"

## 系统配置
- 12AI API: https://cdn.12ai.org
- 飞书 App: cli_a9f1b6fb6b3bdbc2
- Discord / WhatsApp 已配置
- 当前主助手 workspace: /Users/garytan/.openclaw/workspace-dev

## Agent家族(截至 2026-04-08)
- 拉小知 la_xiao_zhi(资讯)
- 拉小数 la_xiao_shu(数据)
- 拉小投 la_xiao_tou(投放)
- 拉小创 la_xiao_chuang(创意,**2026-03-31 首秀,正式上线**)
- 拉小诊 la_xiao_zhen(诊断)
- 拉小码 la_xiao_ma(代码,有每日 cron 日记)

## 本周重要技术结论(2026-04-02~04-08)

### 🔧 模型与隔离会话
- **【04-04 确认】MiniMax-M2.7-highspeed 不支持 tool calls**,导致5个 isolated session(la_xiao_zhi/su/chuang/zhen/da_feng)全部失败
- **修复方案**:将这5个 isolated session 的模型改为 `minimax-cn/MiniMax-Text-01`(已实测支持 tool calls)
- **【04-09 确认】19个 cron 从 isolated → current session 迁移**:Gary 手动触发,减少 isolated session 依赖,晨间 cron 网络故障不再影响 current session cron
- **关键原则**:主会话有 fallback 机制,不等于 isolated session / cron 可用--必须单独验证

### 🎬 小红书视频处理链路(04-06 确认)
- **元数据获取**:MCP / agent-reach 负责搜笔记、拿 note_id / xsec_token / 标题
- **视频下载**:yt-dlp 负责真实下载(不要用 xiaohongshu-mcp 当下载器)
- **音频抽取**:ffmpeg
- **中文转写**:whisper.cpp (`/opt/homebrew/bin/whisper-cli`) + 本地 ggml 模型

### 📦 karpathy-pkm 知识库(04-09 入库完成)
- **重建完成**:历时约10小时(09:29-20:16,04-07)
- **SRC-0082 入库**:Swisse 2026.Q1 京东付费投放复盘(群邑电商)compiled_summary 已写入
- **当前状态**:82 manifests,215 concept pages
- **ISV 目录部分入库**:SRC-0082 已完成;剩余文件待后续 ingest

### 🔁 Cron 已知问题
- **daily-rollup 死锁**:全 Agent 日记依赖 rollup 存在,但 rollup 失败后全部空跑;04-08 触发,需修复为"不存在则自行汇总"
- **AI Builders Digest 重复执行**:cron 重试机制导致同一天跑了两次(09:18 + 09:39)
- **RSS 代理**:04-07 全挂(45/45 failed),04-08 正常但无新内容(历史断连问题仍存在)
- **飞书消息重复入队**:04-02 主会话被300+重复消息淹没,去重机制待查

### 🛠 系统能力(已验证可用)
- **Obsidian CLI**:v1.12.7,`vault = /Users/garytan/Documents/garytan`(04-04 确认)
- **exec 权限**:04-04 从 allowlist miss 恢复可用
- **skills 同步**:workspace-dev/skills 为主公共库(51个),overlay overlay 局部分叉 `vision` 需后续并入

### ⚠️ 待清理项
- `la_xiao_zhen/skills/dist` 疑似构建产物/脏目录,建议清理

### 04-09 新增规则
- **19个 cron 从 isolated → current**:04-09 Gary 触发迁移,减少 isolated session 依赖
- **晨间 cron 持续故障**:isolated session 在 06:00 AM 全部网络失败(04-02 起持续),根因未解,current session 不受此影响
- **daily-rollup 为空时 cron 应自行兜底**:不要等 rollup 生成后再写日记
- **karpathy-pkm SRC-0082 入库完成**:Swisse Q1 京东付费投放复盘(群邑电商),compiled_summary 已写入

### 04-10 新增规则
- **current session cron 不受晨间网络故障影响**:06:10 验证,memory-weekly/backup/ai-news 均成功;isolated session cron 仍然全灭
- **Ontology entity ID 必须全局唯一**:同一项目不能有两个 ID(`project_karpathy_pkm` vs `proj_karpathy_pkm` 导致关系孤儿);新增 entity 前必须检查 existing IDs
- **daily-memory-refresh 可能重复触发**:06:04 和 06:19 两次触发间隔仅15分钟;第二次写入时做了幂等检查,未产生脏数据

---

## 本周新增规则(2026-04-11 整理)

### 系统稳定性
- **【04-11 新增】cron 调度器重复触发问题**:AI Builders Daily Digest 在短时间(<30min)内多次触发,同一天出现多个 dev session 被唤醒;daily-memory-refresh 也观察到此模式(04-10 06:04+06:19);根因未解
- **【04-11 新增】ISV目录部分入库完成**:SRC-0082(Swisse Q1 JD)已入库,当前 82 manifests/215 concept pages;其余文件待继续 ingest

### Gary 工作流
- **【04-11 新增】Swisse Q1 类目对比报告**:完整链路(Gary发图→飞书文档→评论通知→Obsidian补档)已跑通;图片+数据+CBEC数据均已处理

### 记忆系统维护原则
- **【04-11 确认】session entity ID 下划线/横线问题已核实**:session+对应note的"重复"并非真正的session重复,而是 session entity + SummaryNote entity 共享同一 base UUID;这是正确的 paired design,不需要合并
- **【04-11 确认】project entity ID 正确名称**:`project_karpathy_pkm`(非 proj_karpathy_pkm);relation merge 时必须先核实目标 entity 是否真实存在

---

## 本周新增规则(2026-04-12 整理)

### Ontology 维护
- **【04-12 新增】session 注册必须使用真实 agent_id**:memory-daily-cleanup cron 错误使用 `agent_sessions`(不存在)作为 agent_id,导致17个 phantom session entity 被创建,所有 has_session 关系变成孤儿;教训:注册 session 时 agent_id 必须从 agent 主配置读取,不能硬编码或默认
- **【04-12 新增】graph.jsonl 定期审计**:每周整理时检查 orphan relations、duplicate create、phantom entities;本轮清理:18个脏条目 + 17条孤儿 relations;当前:253 entities / 900 relations / 0 orphans
- **【04-12 新增】dafeng openid**:`ou_2b61cfc2e4c54c32e1734a48458b1d76`(04-10 确认,用于跨账号飞书消息路由)

### Gary 工作流
- **【04-12 新增】Swisse Q1 数据口径差异**:CBEC自营表格中肠胃益生菌小计与上级汇总不符;Present/汇报前需 Gary 提供原始Excel核对

## 本周新增规则(2026-04-13 每周整理)

### Ontology 维护
- **【04-13 新增】session entity ID 格式标准化(dash UUID 为 canonical)**:graph 中存在20个 phantom session entities(同一 UUID 但 underscore 格式),canonical 为 dash 格式;phantom entities 的79条 relations 已全部 redirect 到 canonical;phantom entity creates 已删除;当前:270 entities / 937 relations / 0 orphans
- **【04-13 新增】session entity paired design 确认**:13个 `session_*` + `note_session_*` pairs 是正确的成对设计(一个 session entity + 一个 SummaryNote),不是真正的重复注册;session UUID 混用 underscore/dash 是历史遗留 bug,已通过格式标准化解决
- **【04-13 新增】Cron 重复触发系统性观察**:04-12 22:01~22:06 期间 daily-memory-refresh、AI Builders Digest、memory-weekly、ai-news-daily 各出现 dup,间隔 <10min,是同一调度周期内问题;建议方案:cron payload 加幂等 guard(查 state-feed.json lastSentDate)

### Gary 工作流
- **【04-13 新增】AI Builders Digest 幂等方案**:在 cron payload 中加 guard - 发送前查 `~/.openclaw/workspace-dev/tmp/state-feed.json` 的 lastSentDate,若今天(CST)已发过则跳过;实施状态待确认
- **【04-13 新增】dafeng 线活跃**:04-10 dafeng 线收到 Gary Swisse Q1 需求;dafeng session 正常处理;Gary 关注 Sam Altman $100 Pro 档、levie 非结构化数据观点

### 系统稳定性
- **【04-13 确认】晨间 cron 稳定性持续验证**:current session cron 机制04-10~04-13 持续稳定,isolated session 网络故障问题未再触发;19个 cron 迁移效果确认有效
- **【04-13 确认】AI Builders Digest 仍重复触发**:04-11~04-13 持续,幂等 guard 方案已提出但实施状态待 Gary 确认

## 本周新增规则(2026-04-14 每周整理)

### Ontology 维护
- **【04-14 新增】session entity ID 命名规范(强制)**:`session_{agent}_{session_filename_without_ext}`,filename 保持原样(含 dash),不要再做 dash→underscore 替换;所有 session 注册统一由 daily-memory-refresh 执行,避免多源重复注册;graph 中 132 个 legacy underscore 格式 session entity 待下次 weekly 修复(04-21)
- **【04-14 新增】Session ID 格式不一致根因确认**:memory-daily-cleanup 用 underscore 格式注册,daily-memory-refresh 用 dash 格式检查 → 同批 session 被反复重复注册/误清理的循环;修复后应彻底解决

### Gary 工作流
- **【04-14 新增】Obsidian 分析层应用(派样复购)**:Gary 将 Obsidian 定位于"分析层 + 结论层"--原始数据在表格/SQL/多维表格,分析框架、实验记录、结论复盘、策略迭代在 Obsidian;建议建 4 类笔记模板:项目总览 / 每次派样活动 / 复购结果 / 分群洞察;关联:OPPO 抖音营销会议笔记
- **【04-14 新增】ISV 常用分析 Topic 库(未完成)**:Gary 04-13 晚要求整合「ISV 常用分析 Topic 库 0319」中17个项的 markdown → 飞书文档;**状态:待执行**,高优先级
- **【04-14 新增】Swisse Q1 CBEC 口径差异标注**:肠胃益生菌小计与上级汇总不符;汇报前需 Gary 提供原始 Excel 核对

### 系统稳定性
- **【04-14 确认】AI Builders Digest 幂等 guard 有效**:state-feed.json lastSentDate 检查生效(04-13 daily-rollups 正常);重复触发问题已缓解(未根除)
- **【04-14 确认】daily-rollups/2026-04-13.md 成功生成**:rollup cron 死锁短暂缓解,但根因未修复(cron 不应在 rollup 不存在时等待,应自行兜底)
- **【04-14 确认】Cron 迁移效果持续稳定**:current session cron 04-10~04-14 持续正常,isolated session 网络故障未再触发

## 本周新增规则(2026-04-24 每周整理)

### Gary 工作流
- **【04-22 新增】la_xiao_chuang 结束10天休眠**：Gary 14:58 向 la_xiao_chuang 发送 Claude Design 进阶审美与设计准则30条，要求整合进 `bggg-ppt-design` 系统；la_xiao_chuang 据此生成"广州AI大赛&生日会"WPP 图片，发送飞书群组。设计原则已沉淀到创意 Agent
- **【04-22 新增】抖音618营销活动**：Gary 主 session（6.6MB）涉及抖音618营销活动图片素材分发（page3_category、page6_requirements、page4/5_creatives），通过飞书群组发送。性质：媒介协调/创意分发
- **【04-20 新增】xhs-ad-analyst skill 真实化**：commit `6df1b9b` 接入飞书 Spreadsheet 数据源（`WeZosdIg4hWvWMt0qj5cBqeUnvb`）+ 实际基准值（Content Type / 平台 / CPC / CPUV），真正可复用的自动化工具

### karpathy-pkm 项目状态
- **【04-17 新增】新批次入库**：SRC-0102（京东广告产品手册）+ SRC-0103（618大促营销指南）；Manifest 编号漂移待 Gary 清理
- **【04-17 新增】Obsidian sync 脚本完成**：`obsidian_doc_sync_to_kk.py` 打通（raw/obsidian-docs + inbox/obsidian-docs）；reference-only 策略切换完成

### 系统稳定性
- **【04-24 确认】Ontology 格式问题已修复**：993条旧格式 entries 全部转换为标准 entity.id 格式；验证：1465 entities / 0 errors / 0 orphans ✅（历史最佳）
- **【04-22 确认】RSS 代理持续故障**：s.ztso.xyz:11211 Connection refused，04-18~04-22 连续5天空转；备用代理方案未落地
- **【04-20 确认】RSS 恢复后再次空转**：04-20 恢复34条精选后，04-21~04-22 连续0条；根因：7天去重窗口把孤岛内容误判为重复（非代理问题本身，是去重逻辑边界 case）

### 跨账号线索（dafeng / xiaofeng / la_xiao_xxx）
- **【04-16 新增】dafeng 线活跃**：Gary 通过 dafeng 账号（ou_2b61cfc2e4c54c32e1734a48458b1d76）讨论 Claude Code 桌面端、Levie FDE 观点
- **【04-22 新增】la_xiao_* 全员正常**：la_xiao_zhi/su/tou/zhen/ma 日记 cron 正常完成；la_xiao_chuang 结束10天休眠恢复产出
- **【04-24 确认】Gary 回归**：04-22~04-23 Gary 打破10天沉默，主 session 恢复活跃（6.6MB + 537KB）

---

## 本周新增规则(2026-04-15 每周整理)

### karpathy-pkm / Obsidian 工作流
- **【04-15 新增】Obsidian 文档入库改为 reference-only**:`obsidian_doc_sync_to_kk.py` 不再复制正文到 raw/sources,而是生成 reference stub,并在 manifest 记录 `source_path` / `obsidian://` 路径,减少重复存储
- **【04-15 新增】reference compile 前置链路已补齐**:已新增 `kk_reference_source_backfill.py`(历史 manifest 回填 source_path + 生成 stub)与 `kk_reference_compile_prep.py`(按 manifest 回读原文并生成 compile queue);**但最后一步"把 compile 结果写回 manifest.compiled_summary 并更新 wiki"仍未自动化**,后续需补 reference compile runner 才算闭环
- **【04-15 新增】Gary Obsidian 定位**:Obsidian = 分析层 + 结论层。原始数据在表格/SQL/多维表格;分析框架、实验记录、结论复盘、策略迭代在 Obsidian。建议4类笔记模板:项目总览 / 每次派样活动 / 复购结果 / 分群洞察。关联:OPPO 抖音营销会议笔记

### Gary 新需求(待执行)
- **【04-13 晚新增】ISV 常用分析 Topic 库 0319 → 飞书文档**:Gary 要求把17个分析项的所有 markdown 整合成一个飞书文档。**状态:需求已接收,待执行**,高优先级

### 系统稳定性
- **【04-15 确认】所有 Agent 日记 cron(22:00~23:35 批次)全部 OK**:小风/小诊历史 timeout consecutiveErrors 已清零;当前稳定
- **【04-15 确认】memory-daily-cleanup isolated 仍有偶发 timeout**(consecutiveErrors=1);建议改为 current session
- **【04-15 新增】重复 cron job 需合并**:`memory-weekly-review`(job id: 7ba8f37d,调用 python 脚本)和 `weekly-memory-review`(job id: 4e8977d3,调用 agent prompt)两套并行;建议禁用 `weekly-memory-review`,保留 `memory-weekly-review`(python-script 版本更稳定)

### 待补盲区(04-15 整理)
- 🔴 ISV Topic 库 0319 → 飞书文档(Gary 明确需求,**待执行**)
- 🔴 karpathy-pkm reference compile runner(最后一步未闭环)
- 🔴 Session entity ID 格式修复(132 个 legacy underscore 格式,**04-21 前**,已拖延一周)
- 🔴 daily-rollup cron 死锁根因(04-09~04-15 持续,rollup 不存在时自行兜底)
- 🔴 重复 cron job 合并(`memory-weekly-review` vs `weekly-memory-review`)
- 🟡 ISV Daily Sync 中文路径编码(`宇先生/Documents/ISV`,04-11 起持续)
- 🟡 Cron 调度器重复触发根因(幂等 guard 缓解,调度器层面待查)
- 🟡 memory-daily-cleanup 改为 current session(isolated 偶 timeout)

---

## 本周新增规则(2026-04-25 每周整理)

### Ontology 维护
- **【04-25 新增】4个重复 session entity IDs 已修复**:graph.jsonl 中4个 session entity 存在2~3个副本(来自跨 refresh 周期的重复注册);已删除副本,保留最早记录;修复后验证:1517 entries / 424 domain entities / 1093 relations / 0 duplicates / 0 orphans / 0 errors ✅;备份:graph.jsonl.bak_04_25 系列
- **【04-25 新增】daily-memory-refresh 跨日重复注册根因**:同一 session UUID 在跨日时被重复注册;修复方向:在注册前检查 entity ID 是否已存在(is_idempotent check)
- **【04-25 确认】Topic/Rule/SummaryNote 全部 unique ID**:10 Topics / 9 Rules / 27 SummaryNotes,全部无重复ID ✅

### Gary 工作流
- **【04-25 新增】Gary 沉默是工作节奏,不是系统问题**:04-19~04-21(3天沉默)和 04-24~04-25(2天沉默,全天合计仅5字)两次观察到;系统应在 Gary 沉默时正常自转,不需要主动干预;沉默后首次回归时主动汇报本周系统状态
- **【04-25 新增】RSS Feishu card 格式已验证可行**:04-23 interactive card(21个可点击按钮)用户体验良好;后续 RSS 精选统一使用此格式

### 系统稳定性
- **【04-25 新增】RSS 代理已到必须推动解决的节点**:s.ztso.xyz:11211 持续7天+ Connection refused;04-20 短暂恢复后再次死亡;去重逻辑边界 case 也已失效;不能再靠"跳过digest"维持,必须主动联系 IT 或切换替代来源
- **【04-25 确认】Gary 全天沉默时系统正常自转**:04-24~04-25 Gary 沉默2天,全 Agent 每日日志正常完成(cost=$2.47),WhatsApp Gateway 偶发抖动后自动恢复,ISV Daily Sync 正常运行;系统自转能力已验证

### 跨账号线索
- **【04-25 确认】la_xiao_chuang design-standards skill 已升入主库**:30条 Claude Design 准则已整合进 bggg-ppt-design 系统;skill 从 agent-private 升入 workspace-dev/skills 主库,可供其他创意 Agent 复用
- **【04-25 确认】dafeng 本周无新会话**:04-19~04-25 dafeng 账号无主动消息;Gary 主要通过 xiaofeng(主账号)互动

## 本周新增规则(2026-04-26 整理)

### 系统稳定性
- **【04-25 新增】RSS 精选三重故障隔离缺失**：飞书 IM/Doc token 失败 + MiniMax-Text-01 模型 503 + JSON 序列化崩溃，三环全崩但数据采集本身成功；修复方向：将各环节拆分错误处理，任何一步失败只影响自己，不死整条链路
- **【04-23 新增】RSS Feishu card 格式验证成功**：21个可点击按钮 interactive card 用户体验良好；后续 RSS 精选统一使用此格式
- **【04-25 新增】ISV 入库本周首次完整闭环**：SRC-0104/0105 7步全通过，久违的成就感；但 SIGKILL 问题仍在（04-25 ISV Daily Sync）

### Gary 工作流
- **【04-25 新增】Gary 沉默规律确认**：04-19~04-21（3天）+ 04-24~04-25（2天）两次沉默观察；沉默是工作节奏，系统保持自转；沉默后首次回归时主动汇报本周系统状态
- **【04-22~04-23 新增】la_xiao_chuang 恢复产出**：30条 Claude Design 准则整合，WPP 图片成功生成发送；创意 Agent 能力升级

### 记忆系统
- **【04-23 新增】agent_tips_summary.md**：10条精华实战经验，Gary 04-23 请求生成
- **【04-25 新增】重复 session entity ID 跨日注册根因**：daily-memory-refresh 在跨日时对已存在的 entity 未做幂等检查；修复：在注册前检查 entity 是否已存在

## 本周新增规则(2026-04-27 整理)

### Ontology 维护
- **【04-27 新增】1个重复 SummaryNote 已清理**：`note_session_la_xiao_chuang_4c4c8e09_6320_4cd3_866c_157c76bda727`（underscore，无 created 时间戳）与 canonical dash 版本重复；删除 underscore 版本；SummaryNote 27→26 ✅；备份：graph.jsonl.bak_04_27_weekly
- **【04-27 新增】141 条 old-format `relate` 条目仍存在**：04-24 修复 993 条后仍有 141 条（来自后续 cron）；不影响功能，建议下次 ontology 大规模刷新时统一迁移
- **【04-27 确认】Ontology 状态**：1841 entries / 464 Sessions / 1091 Relations / 26 SummaryNotes / 0 orphans ✅

### Gary 工作流
- **【04-27 新增】Gary 沉默已成常态**：04-19~04-21（3天）+ 04-24~04-27（4天）= 本周沉默 7 天；系统自转完全正常，无需主动干预；沉默后首次回归时主动汇报本周系统状态
- **【04-27 新增】ISV 入库本周首次完整闭环（04-25）**：SRC-0104/0105 7步全通过（raw→文本提取→Manifest→MiniMax摘要→kk_compile→Feishu DM→isv_last_run）；SIGKILL 偶发但未阻断本次闭环

### 系统稳定性
- **【04-27 确认】RSS 代理已死 9天+**：s.ztso.xyz:11211 Connection refused 持续；04-25/04-26 精选均缺口；必须推动 IT 解决，不能再靠跳过维持
- **【04-27 新增】RSS 三重故障修复方向**：将 Feishu token 获取、MiniMax 调用、JSON 序列化拆开处理；任何一步失败只影响自己，不死整条链路

### 跨账号线索
- **【04-27 确认】dafeng 本周 0 新 session**：最后活跃 04-16~04-17；账号完全沉默
- **【04-27 确认】la_xiao_* 全员实质沉默**：24个 cron session，全部空内容；无实质 Agent 产出
- **【04-27 确认】重复 cron 并行仍未合并**：`memory-weekly-review` vs `weekly-memory-review` 仍两套并行（自 04-15 起已 12 天）；建议：禁用 `weekly-memory-review`，保留 `memory-weekly-review`（python-script 版本更稳定）

