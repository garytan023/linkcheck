# 每周记忆回顾报告 | 2026-04-12

> 时间范围：2026-04-06 ~ 2026-04-12
> 整理时间：2026-04-12 06:09 AM (Asia/Shanghai)
> 整理依据：memory/ 日记（04-06~04-11）+ ontology graph + WARM/HOT/MEMORY.md

---

## 一、本周新增了什么

### 1. Ontology 大清理（最大事件）
- **18个脏条目一次性清除**：
  - 17个 phantom `session_sessions_*` entries（来自 `memory-daily-cleanup` cron 错误使用不存在的 `agent_sessions` 作为 agent_id）
  - 1个重复 `SummaryNote` entity（`note_proj_karpathy_pkm_status_20260411` 有两个 create）
- **17条孤儿 relations 同步清除**
- 清理后：253 entities / 900 relations / **0 orphans** ✅
- **根因**：`memory-daily-cleanup` cron 在注册 session 时错误读取了 `agent_sessions` 而非真实 agent（`agent_dev` / `agent_assistant`）

### 2. Swisse Q1 工作流深化（04-10凌晨）
- Gary 追加 CBEC 自营/大贸自营数据（跨境自营 24个三级类目 + 大贸自营 21个三级类目）
- 追加第六章，CBEC小结：跨境自营 79.9M→80.5M（-1%）；大贸自营 86.3M→102.7M（+19%）
- **⚠️ 数据口径差异**：肠胃益生菌小计与上级汇总不符，Present 前需 Gary 提供原始 Excel 核对

### 3. Cron 稳定性持续（04-10验证）
- current session cron 机制持续稳定；isolated session cron 全灭问题未再触发
- 19个 cron 已迁移至 current session（04-09 Gary 手动），04-10 晨间验证正常

### 4. 本周新增 Ontology 实体
| Rule ID | 内容 | 时间 |
|---------|------|------|
| rule_ai_builders_duplicate_cron | AI Builders Digest 重复触发 | 04-11 |
| rule_isv_partial_ingestion_done | ISV目录SRC-0082入库完成 | 04-11 |
| rule_memory_cleanup_agent_sessions_bug | memory-daily-cleanup错误agent_id导致phantom entries | 04-12 |

---

## 二、清理了什么

### 1. Ontology 一致性修复
- 17个 phantom `session_sessions_*` entities 全部删除（real sessions 已用正确 ID 存在）
- 17条 has_session orphan relations 全部删除
- 1个重复 SummaryNote create 删除（保留更准确的第二个版本）
- 0 orphans remaining ✅

### 2. 三层记忆归并
- HOT_MEMORY.md：更新最后更新时间，追加04-12清理记录和历史遗留脏数据说明
- WARM_MEMORY.md：追加4条新规则（dafeng openid、memory-daily-cleanup bug、数据口径差异、graph审计）
- MEMORY.md：追加04-12每周整理条目

---

## 三、跨 Agent / 跨账号重要线索

### Agent 账号分布（截至 04-12）
| Agent | 飞书账号 | 用途 | 状态 |
|-------|---------|------|------|
| dev（小拉风）| xiaofeng | 统筹/主控/记忆系统 | 持续活跃 |
| dafeng | xiaofeng/dafeng | 辅助会话/跨账号 | 04-10 活跃（Swisse Q1需求） |
| la_xiao_zhi | xiaofeng | 资讯/知识库 | 活跃 |
| la_xiao_shu | xiaofeng | 数据分析 | 活跃 |
| la_xiao_tou | xiaofeng | 媒介投放 | 活跃 |
| la_xiao_chuang | xiaofeng | 创意设计师 | 活跃 |
| la_xiao_zhen | xiaofeng | 素材诊断 | 活跃 |
| la_xiao_ma | xiaofeng | 程序员 | 活跃 |

### 关键项目线索
- **karpathy-pkm**：ISV 部分入库（SRC-0082完成）；剩余文件待继续 ingest；ontology entity 正确名称：`project_karpathy_pkm`
- **Swisse Q1 工作流**：图片→飞书文档→CBEC数据→Obsidian 补档，完整链路跑通；⚠️数据口径问题需 Gary 提供原始 Excel 核实
- **cron 稳定性**：isolated session 依赖已移除；memory-daily-cleanup cron 引入 phantom session bug，需监控

---

## 四、补录到长期记忆的条目

| 条目 | 目标层 | 内容摘要 |
|------|--------|---------|
| dafeng openid | WARM_MEMORY | `ou_2b61cfc2e4c54c32e1734a48458b1d76` |
| memory-daily-cleanup bug | WARM_MEMORY | session注册必须用真实agent_id |
| graph定期审计 | WARM_MEMORY | 每周检查orphan/dup/phantom |
| Swisse数据口径差异 | WARM_MEMORY | 肠胃益生菌小计不符，需Gary原始Excel核实 |
| agent_sessions phantom根因 | MEMORY.md | cron错误读取agent_id导致phantom entries |
| 04-12清理结果 | HOT_MEMORY | 253e/900r/0o |

---

## 五、待补盲区

1. **ISV 目录剩余文件 ingest**：路径已知（`~/宇先生/Documents/ISV`），何时继续由 Gary 决定
2. **memory-daily-cleanup cron bug 根因**：session 注册时错误读取 `agent_sessions` 而非真实 agent_id；是否修复以及是否向 Gary 报告待确认
3. **dafeng 线消息路由机制**：dafeng 收到 Gary 消息后如何通知主会话，是否有明确工作流？
4. **Cron 调度器重复触发**：AI Builders Digest + daily-memory-refresh 短时间多次触发，根因未解

---

## 六、Ontology 一致性验证结果（04-12）

| 检查项 | 结果 |
|--------|------|
| 总实体数 | **253**（-18脏条目） |
| 总关系数 | **900**（-17孤儿） |
| Entity ID 重复 | 无 ✅ |
| Orphan relations | **0** ✅ |
| Schema 验证 | 通过（14 types, 9 relation types）|
| Session entities | 175（-17 phantom） |
| SummaryNote | 26（-1 duplicate） |
| 本次清理总量 | 18 creates + 17 relations = 35条 |
