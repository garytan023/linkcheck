# 每周记忆回顾报告 | 2026-04-08

> 时间范围：2026-04-02 ~ 2026-04-08
> 整理时间：2026-04-08 10:27 AM (Asia/Shanghai)
> 整理依据：memory/daily/ + ontology + MEMORY.md + WARM_MEMORY.md + HOT_MEMORY.md

---

## 一、本周新增了什么

### 1. 知识库重建（最大事件）
- **karpathy-pkm 全面重建**：04-07，历时约10小时
  - 37 sources，215 concept pages
  - Jerman 批次200个概念页 sources/triple-bracket bug 和定义截断修复
  - `compiled_summary` 字段升级为 dict 结构（含 title/content/sources）
- **ISV 目录确认未入库**：路径 `/Users/garytan/Documents/garytan/宇先生/Documents/ISV`，6个文件待 ingest → karpathy-pkm

### 2. 系统修复
- **MiniMax isolated session 模型修复**：04-04 确认 `MiniMax-M2.7-highspeed` 不支持 tool calls，5个 agent（la_xiao_zhi/su/chuang/zhen/da_feng）改为 `MiniMax-Text-01`
- **Obsidian CLI 打通**：v1.12.7，vault=`/Users/garytan/Documents/garytan`（04-04）
- **exec 权限恢复**：`allowlist miss` 修复（04-04）
- **Ontology 增量**：04-08，新增34个 sessions，修复 `session_assitant`→`session_assistant` 拼写错误（77处替换）

### 3. 新增规则与结论
- **Gary 直接消息规则**（04-03）：收到 Gary 直接消息 → 简短"ok"确认，不需要展开
- **小红书视频处理链路**（04-06）：MCP/agent-reach（metadata）→ yt-dlp（下载）→ ffmpeg（音频）→ whisper.cpp（转写）
- **Cron 无循环依赖原则**：cron job 失败时自行兜底，不能依赖前置文件存在

### 4. 新增 Ontology 实体（本次整理追加）
- Rule: `rule_gary_ok_only`, `rule_xhs_video_pipeline`, `rule_cron_no_circular_deps`
- Project: `project_karpathy_pkm`
- SummaryNote: 04-02 cron灾难日、04-04模型修复、04-06 XHS链路、04-08 rollup死锁

---

## 二、本周清理了什么

### 1. Ontology 修复
- `session_assitant_*` → `session_assistant_*`（7条关系 × 11个session，77处替换，04-08完成）
- 移除04-08 heredoc错误写入的4行无效JSON（644行 → 重写为656行valid JSONL）

### 2. HOT Memory 归档
- 合并 HOT_MEMORY.md（删除过时条目，新增本周完成项标记）

### 3. 重复条目清理
- MEMORY.md：`### 2026-03-10` 合并为一条，`### 2026-03-10 晚` 冗余条目删除
- MEMORY.md：Skills 列表去重，ISV 目录重复条目合并

### 4. Schema 一致性
- graph.jsonl Schema.yaml 验证通过：12种 entity types，10种 relations，全部合规

---

## 三、跨 Agent / 跨账号重要线索

### 各 Agent 状态
| Agent | 账号 | 本周状态 |
|-------|------|---------|
| dev（主控）| xiaofeng | 主要执行者，日记 cron / 知识库 / 系统修复 |
| assistant（分身）| xiaofeng / dafeng | 辅助会话，04-01~04-08 多 session |
| la_xiao_zhi | xiaofeng | **模型已修复**（Text-01），日报脚本待验证 |
| la_xiao_shu | xiaofeng | 数据分析，模型已修复 |
| la_xiao_tou | xiaofeng | 投放，模型已修复 |
| la_xiao_chuang | xiaofeng | 创意，模型已修复，04-07 无独立产出 |
| la_xiao_zhen | xiaofeng | 诊断，模型已修复 |
| la_xiao_ma | xiaofeng | 代码，每日 cron 日记 |

### 权限问题
- `exec.ask` 受保护字段，无法在线修改；需手动编辑 `~/.openclaw/openclaw.json`
- feishu_doc 工具使用用户授权绕过 APP token 写入限制（已稳定）

### 技术债演进
- 04-02：灾难日（8/9 cron 失败 + 300+ 消息重复）
- 04-04：模型修复曙光（Text-01 替换）
- 04-07：知识库重建完成，但 RSS 持续断连
- 04-08：rollup cron 死锁再次暴露架构脆弱性

---

## 四、补录到长期记忆的条目

| 条目 | 写入位置 | 内容摘要 |
|------|---------|---------|
| Gary OK规则 | WARM_MEMORY.md | 直接消息→简短ok，不需要展开 |
| karpathy-pkm状态 | MEMORY.md | 37 sources/215 pages，ISV未入库 |
| XHS视频链路 | MEMORY.md + ontology | 4步链路：MCP/agent-reach→yt-dlp→ffmpeg→whisper |
| 模型修复结论 | WARM_MEMORY.md | MiniMax-Text-01替换isolated session M2.7 |
| ISV目录路径 | MEMORY.md + HOT | ~/宇先生/Documents/ISV |
| Cron无死锁原则 | HOT_MEMORY.md | cron失败自行兜底 |
| karpathy-pkm项目 | ontology | project_karpathy_pkm实体+关系 |
| Gary OK规则 | ontology | rule_gary_ok_only实体+关系 |
| XHS链路规则 | ontology | rule_xhs_video_pipeline实体+关系 |

---

## 五、待补盲区

### 🔴 高优先级（影响 Gary 需求闭环）
1. **ISV 目录入库**：Gary 已确认需求，路径已知，6个文件待 ingest
2. **daily-rollup cron 死锁**：04-08 再次触发，全 Agent 日记零产出；需修改 rollup cron 为"不存在则自行汇总"

### 🟡 中优先级（系统稳定性）
3. **RSS 代理长期断连**：约从 03-20 持续至今，04-07 全挂（45/45），04-08 正常但 0 条新内容
4. **飞书消息重复入队**：04-02 主会话被 300+ 重复消息淹没，消息队列去重机制待查
5. **AI Builders Digest 重复执行**：cron 重试导致一天跑两次（04-08）

### 🟢 低优先级（系统整洁）
6. **`la_xiao_zhen/skills/dist` 脏目录**：疑似构建产物，建议清理
7. **skills overlay 分叉**：`workspace-dev/.agents/skills/vision` 未并入主库
8. **memory plugin 语义召回 401**：已知降级策略，不影响主功能
9. ** ontology sessions 噪声**：115个 Session 实体中，部分标记为 `topic_tags:["general"]` 的日常会话价值有限；建议下轮整理做 session pruning（按最后活跃时间过滤）

---

## 六、Ontology 一致性验证

| 检查项 | 状态 |
|--------|------|
| JSONL 语法 | ✅ 656行，全部 valid |
| Schema 合规 | ✅ 12 entity types / 10 relations，全部匹配 schema.yaml |
| 拼写一致性 | ✅ session_assistant（126处），0 session_assitant |
| Entity 总数 | 185 entities |
| Relation 总数 | 471 relations |
| Referenced entities | ✅ 所有 relate 的 from/to entities 均存在于 entities 中 |
| New entries (2026-04-08) | ✅ 12条新增（Project×1, Rule×3, SummaryNote×4, Relation×4）|

---

*下次周整理：2026-04-15（周三）*
*本次整理执行 session: weekly-memory-review cron (7ba8f37d-b763-439d-9058-066380bd9ce7)*
