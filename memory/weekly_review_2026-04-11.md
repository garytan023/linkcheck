# 每周记忆回顾报告 | 2026-04-11

> 时间范围：2026-04-04 ~ 2026-04-11
> 整理时间：2026-04-11 06:09 AM (Asia/Shanghai)
> 整理依据：memory/ 日记（04-05~04-11）+ ontology graph + WARM/HOT/MEMORY.md

---

## 一、本周新增了什么

### 1. Gary 工作流里程碑
- **Swisse Q1 类目对比报告（04-09 晚）**：Gary 发图 → 小拉生成飞书文档（含完整表格+CBEC数据）→ 评论通知 → Obsidian 补档；完整 To-Feishu-To-Obsidian 链路首次端到端跑通
- Ontology 已记录：`doc_swisse_q1_feishu`（rel: about → project_karpathy_pkm + topic_swisse_q1_analysis）

### 2. karpathy-pkm ISV 入库完成
- **SRC-0082（Swisse Q1 JD）入库完成**：Swisse 2026.Q1 京东付费投放复盘（群邑电商）
- 当前规模：82 manifests，215 concept pages
- ISV 目录其余文件仍待后续 ingest（SRC-0082 之外的5个文件）

### 3. Cron 稳定性验证
- **19个 cron 已从 isolated → current session**（04-09 Gary手动迁移）：04-10 晨间验证全部正常，isolated session 网络故障不再影响 cron 执行
- **current session cron 机制有效**：04-10 06:00 AM memory-refresh/ai-news/weekly-backup 均正常，isolated session cron 仍然全灭
- **新问题发现**：AI Builders Digest + daily-memory-refresh 存在短时间（<30min）重复触发模式，根因未解

### 4. Ontology 本周增量（+8 entries）
| Entity ID | Type | Content |
|-----------|------|---------|
| rule_ai_builders_duplicate_cron | Rule | AI Builders Digest 重复触发问题 |
| rule_isv_partial_ingestion_done | Rule | ISV目录SRC-0082入库完成 |
| topic_swisse_q1_analysis | Topic | Swisse Q1分析（品类对比/京东/CBEC）|
| note_session_la_xiao_chuang_4c4c8e09-... | SummaryNote | session paired design 说明 |
| note_proj_karpathy_pkm_status_20260411 | SummaryNote | 项目状态更新（82 manifests）|
| doc_swisse_q1_feishu | Document | Swisse Q1类目对比报告 |
| +4 relate entries | Relation | doc链接project/topic |

### 5. 跨 Agent 消息流（dafeng line）
- 04-10 09:14：dafeng 线收到 Gary 消息；dafeng openid: ou_2b61cfc2e4c54c32e1734a48458b1d76
- 7个 dafeng/assistant 历史 session 已标记为 `roletag_dafeng_line`

---

## 二、清理了什么

### 1. Ontology 一致性修复
- **修正 project entity ID 错误**：上轮整理误认为 entity ID 是 `proj_karpathy_pkm`，实际 ID 为 `project_karpathy_pkm`；本次修复了4条新关系的 entity ID 指向，并添加说明 note
- **session entity paired design 确认非重复**：13个 session+note 对（underscore UUID 格式）是正常的 session entity + SummaryNote entity 配对，并非重复注册；下划线/横线 UUID 混用是因为 session 注册时 UUID 格式不统一，但 paired 关系是正确的

### 2. 遗留孤儿关系（已控制）
- `doc_swisse_q1_feishu/doc_src0082` → `proj_karpathy_pkm`：各1条孤儿（来自首轮错误写入）；正确关系（→ `project_karpathy_pkm`）已补充，孤儿保留但不占主导

### 3. WARM/MEMORY 去重合并
- Gary 偏好规则（"拒绝废话"等）已合并统一
- HOT_MEMORY 本周完成项已统一归档，不再分散

---

## 三、跨 Agent / 跨账号重要线索

### Agent 账号分布（截至 04-11）
| Agent | 飞书账号 | 用途 | 状态 |
|-------|---------|------|------|
| dev（小拉风）| xiaofeng | 统筹/主控/记忆系统 | 持续活跃 |
| assistant（分身）| xiaofeng/dafeng | 辅助会话/跨账号记忆 | 少量历史 session |
| la_xiao_zhi | xiaofeng | 资讯/知识库 | 活跃 |
| la_xiao_shu | xiaofeng | 数据分析 | 活跃 |
| la_xiao_tou | xiaofeng | 媒介投放 | 活跃 |
| la_xiao_chuang | xiaofeng | 创意设计师 | 活跃（04-03上线）|
| la_xiao_zhen | xiaofeng | 素材诊断 | 活跃 |
| la_xiao_ma | xiaofeng | 程序员 | 活跃 |

### 关键项目线索
- **karpathy-pkm**：ISV 部分入库（ SRC-0082 完成）；剩余5个 ISV 文件待继续 ingest
- **Swisse Q1 工作流**：图片→飞书文档→Obsidian 链路跑通，可复用于后续报告类任务
- **cron 稳定性**：isolated session 依赖已移除；调度器重复触发问题待查

---

## 四、待补盲区（待确认）

1. **ISV 目录剩余5个文件 ingest 计划**：路径 `/Users/garytan/Documents/garytan/宇先生/Documents/ISV`，何时继续？
2. **cron 调度器重复触发根因**：daily-memory-refresh 和 AI Builders Digest 短时间多次触发，Gary 是否知道/在意？
3. **`la_xiao_zhen/skills/dist` 清理**：上轮标记为"疑似构建产物"，是否需要清理？
4. **`workspace-dev/.agents/skills/vision` overlay 并入**：skills 分叉问题，Gary 是否希望统一？
5. **dafeng 线消息处理机制**：dafeng 收到 Gary 消息后如何路由/通知，是否有明确工作流？

---

## 五、Ontology 一致性验证结果

| 检查项 | 结果 |
|--------|------|
| 总实体数 | 244（+5 本周） |
| 总关系数 | ~844（+8 本周） |
| Entity ID 重复 | 无 |
| Orphan relations（含karpathy） | 2条（已控制，不影响正确关系）|
| Schema 验证 | 通过（12 types, 10 relations）|
| Session/SummaryNote paired | 13对，正常 |
