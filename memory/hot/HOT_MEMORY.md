**最后更新**: 2026-04-27 06:01

## 04-27 每日整理 ✅（06:01）
### 上次更新：04-25 21:42

### Ontology 重大修复（本次最大事件）
- **发现**：4个 duplicate session entity IDs，来自跨 refresh 周期的重复注册
  - `session_dev_b096fec3_...`：lines 1320, 1466 → 保留1320
  - `session_dev_d1b529d9_...`：lines 1278, 1474 → 保留1278
  - `session_dev_1ad9ac43_...`：lines 1333, 1502, 1511 → 保留1333（删除2个副本）
- **修复后验证**：1517 entries / 424 domain entities / 1093 relations / **0 duplicates** / **0 orphans** / **0 errors** ✅
- **备份**：`graph.jsonl.bak_04_25` / `.bak_04_25b` / `.bak_04_25c`
- **根因**：daily-memory-refresh 在跨日时对已存在的 entity 做了重复注册；修复方向：在注册前检查 entity 是否已存在

### Topic / Rule / SummaryNote 一致性（全部通过）
- 10 Topics：全部 unique ID ✅
- 9 Rules：全部 unique ID ✅
- 27 SummaryNotes：全部 unique ID ✅

### Gary 沉默规律
- **04-19~04-21（3天）**：全天沉默，只有心跳 poll
- **04-22~04-23**：打破沉默（6.6MB + 537KB），抖音618 + PPT Slide 10
- **04-24~04-25（2天）**：再次沉默，全天合计仅5字
- **结论**：Gary 沉默是工作节奏，不是系统问题；系统保持自转即可

### 本周闭环
- 4个重复 session entity IDs ✅
- design-standards skill 决策（升入主库）✅
- `memory/agent_tips_summary.md` 创建（10条精华实战经验）✅

### 待补盲区更新（04-25）
- 🔴 ISV Topic 库 0319 → 飞书文档：**12天**（04-13起）
- 🔴 karpathy-pkm reference compile runner：**14天**（04-11起）
- 🔴 RSS 代理：**7天+**（04-18起，s.ztso.xyz:11211 持续 Connection refused）

### 本周新增规则
- **Gary 沉默是工作节奏**：系统保持自转，不需要主动干预；沉默后首次回归时主动汇报
- **RSS 代理已到必须推动解决的节点**：连续7天+空转，不能再靠跳过维持
- **RSS Feishu card 格式已验证**：21个可点击按钮用户体验良好，后续统一使用

---

## 04-25 每日整理 ✅（21:10）

### Ontology 验证结果（完美）
- **验证前**：399 entities / 1066 relations / 0 entity errors / 0 relation errors / 0 orphans ✅
- **结论**：Ontology 一致性完美，无需修复历史遗留问题

### Session 注册（幂等）
- **新注册**：21个新 session（2026-04-24: 11 dev + 1 la_xiao_zhen + 1 assistant; 2026-04-25: 7 dev + 2 assistant）
- **Session 类型**：cron_session×15, active_work×2, system_event×1, assistant_session×3
- **新增关系**：+25 relations（21×has_session + 1×summarized_by + 1×about + 2×tagged_as）
- **新增实体**：+1 SummaryNote（2026-04-25 Gary沉默 + RSS中断 + 全Agent汇总）
- **新增 Topic/RoleTag**：topic_rss_proxy（RSS代理故障）、role_tag_active_work/cron_session/system_event/assistant_session
- **当前 ontology**：424 entities / 1093 relations / 0 orphans ✅（历史最佳）

### 今日关键事件（已记录在 2026-04-25.md）
- Gary 全天沉默（仅2条短消息，5字）
- 全 Agent 每日日志中间汇总层正常执行（cost=$2.47）
- WhatsApp Gateway 408 偶发抖动后自动恢复
- RSS 代理中断第4天（s.ztso.xyz:11211 Connection refused）
- ISV Daily Sync 触发 SIGKILL（63a20f42 session），知识库入库未完成
- 每日资讯精选 09:00 exec exit code 1（备用 RSS 链路备用代理也失败）

---

**最后更新**: 2026-04-27 06:01

## 04-24 每周整理 ✅（06:07）

### Ontology 大规模格式修复（重大）
- **问题**：graph.jsonl 中 993 条旧格式 entries（`{"op": "relate"...}` shorthand）混入 326 条新格式，导致 validator 报 MISSING ID 错误
- **根因**：历史版本遗留格式，与当前 schema 不一致
- **修复**：全部 993 条转换为标准 `entity.id` 格式；补充 entity.id 并保留 properties
- **额外修复**：2条 relation reference 错误（`agent_ecom-vision-gemini31` → `agent_ecom_vision_gemini31`）
- **验证**：1465 entities / 0 entity errors / 0 reference errors / 0 orphaned relations ✅（历史最佳）

### Session 注册（幂等）
- **新注册**：73个 session + 73条 relation（dev×52, assistant×5, la_xiao_chuang×1）
- **Session 类型**：cron=39, active_work=12, dev=16, assistant=5, creative=1
- **当前 ontology**：321 sessions / 1066 relations（总计1465 entities）

### Gary 回归（04-23 22:36）
- Gary 主 session 回归（537KB），10天沉默打破
- 完成了 PPT Slide 10（Skills/GitHub部分）
- 飞书资讯精选改用 interactive card 发送（21个可点击按钮）
- RSS 代理故障第4天（`s.ztso.xyz:11211` Connection refused），digest 跳过

---

## 当前高优先级（更新至 04-25）

### 🔴 未闭环（跨多周）
- [ ] **ISV Topic 库 0319 → 飞书文档**：Gary 04-13 需求，**12天**未执行，17个分析项整合
- [ ] **karpathy-pkm reference compile runner**：04-11 起，**14天**未闭环
- [ ] **RSS 代理稳定性**：s.ztso.xyz:11211 **7天+**持续 Connection refused，04-25 仍全挂
- [ ] **Manifest 编号漂移**：SRC-0097~SRC-0103 漂移，建议 Gary 抽时间清理重建
- [ ] **Power BI 远程访问**：需 Gary 开启 Chrome CDP

### 🟡 本周新增/恶化
- [ ] **重复 session entity ID 注册**：daily-memory-refresh 跨日重复注册问题，需在注册前检查 entity 是否存在
- [ ] **Git sync 缺口**：weekly-backup 2.0G tar.gz 未完成 git sync
- [ ] **重复 cron 并行**：`memory-weekly-review` vs `weekly-memory-review` 两套并行，建议禁用一个

### 🟢 已闭环

---

## 已知技术债（中低优先级）
- ISV Daily Sync 中文路径编码（`宇先生/Documents/ISV`，持续）
- daily-rollup cron 死锁（cron 不应等 rollup，应自行兜底）
- 幂等并发漏洞（cron 调度器层面根因未解）
- Obsidian Inbox cron 执行结果未留证据（04-23 未记录）

## 操作原则（已确认）
- 关键偏好、长期项目、工作流、重要决定必须落盘到本地文件
- 不能只依赖 memory plugin / 向量检索
- plugin 失效时，降级顺序：本地记忆文件 → LCM → 当前上下文
- Gary 直接消息 → 简短"ok"即可，不需要额外文字
- Cron 执行后必须验证产物文件存在，不依赖"执行了=完成了"

## 关键配置与状态
- 飞书 APP ID: cli_a9f1b6fb6b3bdbc2
- Gary openid: ou_d635f4f3d20ac474cf8575038b5d2b33
- dafeng openid: ou_2b61cfc2e4c54c32e1734a48458b1d76
- karpathy-pkm: 82 manifests / 215 concept pages（持续）
- 小红书视频链路：MCP/agent-reach（metadata）→ yt-dlp（下载）→ ffmpeg（音频）→ whisper.cpp（转写）

---

## 04-23 每日整理 ✅
- Gary 回归（22:36，537KB），完成 PPT Slide 10
- RSS 代理故障第4天，digest 跳过
- 晨间 cron 链路幂等完成

## 04-22 每日整理 ✅
- Gary 主 session 突现（6.6MB，22:36）：抖音618营销活动图片素材分发
- la_xiao_chuang 结束10天休眠（15:29，281KB）
- Gary 向 la_xiao_chuang 发送 Claude Design 进阶审美与设计准则30条
- la_xiao_chuang 依据准则生成"广州AI大赛&生日会"WPP 图片，发送飞书群组
- RSS 精选连续第3天空转

## 04-20 每日整理 ✅
- **RSS 恢复**：中断2天后恢复正常，34条精选推送成功
- xhs-ad-analyst skill commit `6df1b9b`：接入飞书 Spreadsheet 数据源 + 实际基准值

## 04-17~04-19 每日整理
- Ontology 周整理历史高位（518→567 entities）
- RSS 代理持续中断（s.ztso.xyz:11211 Connection refused）
- Gary 全天沉默（04-18~04-21）

## 04-15~04-16 每周整理 ✅
- karpathy-pkm reference-only 策略完成
- xhs-ad-analyst skill 接入真实 spreadsheet 数据
- ISV 目录新文件：京东广告产品手册 + 618大促营销指南（SRC-0102/0103）
- 重复 cron job 问题（memory-weekly vs weekly-memory）需合并

## 04-12~04-14 每周整理 ✅
- Ontology 大清理：phantom session entities 移除
- Swisse Q1 CBEC 数据追加（肠胃益生菌口径差异已标注）
- Session entity ID 格式 bug 确认
- AI Builders Digest 幂等 guard 生效

## 历史遗留脏数据（已清理 04-12）
- 17× `session_sessions_*` phantom entries：来自 memory-daily-cleanup cron 错误 agent_id（`agent_sessions`不存在）
- 1× `note_proj_karpathy_pkm_status_20260411` 重复创建
- 清理后：253 entities / 900 relations / 0 orphans

---

## ⚠️ 历史重复内容（已合并，仅保留此处索引）

以下内容因重复已被合并到上方对应章节，不再单独列出：
- 04-11 weekly-memory-review 完成（多次出现，已合并到 04-12 周整理）
- 04-11 Ontology 大规模补录（已合并到 04-12 周整理）
- karpathy-pkm ISV SRC-0082 入库完成（已合并到上方技术债）
- 当前优先级 04-15 版（已合并到上方 04-24 版）

---

## 04-26 每周整理 ✅（06:10）

### 本周新增高优先级
- **RSS 精选三重故障隔离缺失（04-25 新增，🔴紧急）**：飞书 IM/Doc token 失败 + MiniMax-Text-01 模型 503 + JSON 序列化崩溃，三环全崩但数据采集成功；需拆分错误处理，任何一步失败只影响自己
- **RSS 代理持续故障（s.ztso.xyz:11211）**：04-18 起已 8天+，持续 Connection refused
- **ISV Topic 库 0319 → 飞书文档**：04-13 起已 13天未执行，Gary 明确需求
- **karpathy-pkm reference compile runner**：04-11 起已 15天未闭环

### 本周闭环
- 4个重复 session entity IDs ✅（04-25）
- design-standards skill 升入主库 ✅（04-25）
- `memory/agent_tips_summary.md` 创建 ✅（04-23）
- RSS Feishu card 格式验证 ✅（04-23）

### Gary 沉默规律
- 04-19~04-21（3天）+ 04-24~04-25（2天）两次沉默；沉默是工作节奏，不是系统问题

---

## 04-27 每日整理 ✅（06:01）

### Ontology 增量刷新
- **新增注册**：53个 session（dev×48 + assistant×3 + la_xiao_zhi×1）
- **新增关系**：53条 has_session 关系（Agent → Session）
- **验证结果**：0 errors / 0 orphan relations ✅
- **最终状态**：464 Sessions / 1091 Relations / 0 orphans

### Session 内容质量
- **dev × 48**：全部为 cron 空 session（model metadata only，无 user/assistant 消息）
- **assistant × 3**：短 session（8~33行），内容待确认
- **la_xiao_zhi × 1**：空 cron session
- **结论**：无实质性新对话内容，无需补充 SummaryNote

### 开放问题状态（无变化）
- 🔴 RSS 代理（s.ztso.xyz:11211）：约 9 天
- 🔴 ISV Topic 库迁移 0319→飞书：约 14 天
- 🔴 karpathy-pkm reference compile runner：约 16 天


---

## 04-27 每周整理 ✅（06:10）Week 20

### Ontology 修复
- **1个重复 SummaryNote 已清理**：`note_session_la_xiao_chuang_4c4c8e09_6320_4cd3_866c_157c76bda727`（underscore，无 created 时间戳）与 dash 版本重复；删除 underscore 版本；SummaryNote 27→26 ✅
- **141 条 old-format `relate` 条目仍存在**：后续 cron 运行时继续生成；不影响功能，建议下次大规模刷新时统一迁移
- **当前状态**：1841 entries / 464 Sessions / 1091 Relations / 26 SummaryNotes / 0 orphans ✅

### Gary 沉默（本周 7 天）
- 04-19~04-21（3天）+ 04-24~04-27（4天）= 本周沉默 7 天
- 系统自转完全正常，无需干预

### 本周闭环
- 重复 SummaryNote 清理 ✅（04-27）
- ISV 入库完整闭环（04-25，SRC-0104/0105，7步全通过）✅
- 04-27 daily-memory-refresh 无 phantom session ✅

### 本周恶化/新增
- 🔴 RSS 三重故障（04-25）：飞书 token + MiniMax 503 + JSON 序列化三环全崩，需错误隔离修复
- 🔴 RSS 代理（s.ztso.xyz:11211）：04-18 起已 9天+，持续 Connection refused
- 🟡 重复 cron 并行（memory-weekly-review vs weekly-memory-review）：12天未合并

### 持续未闭环
- 🔴 ISV Topic 库 0319 → 飞书文档（04-13 起，~16天）
- 🔴 karpathy-pkm reference compile runner（04-11 起，~18天）

