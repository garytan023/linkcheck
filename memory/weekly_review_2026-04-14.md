# 每周整理 | 2026-04-14（第14周）

> 整理时间：2026-04-14 06:07 AM CST
> 覆盖周期：2026-04-07 ~ 2026-04-14
> 撰写者：小拉（主会话 weekly-memory-review cron）

---

## 一、本周新增了什么

### 1. 记忆文件增量（04-07 ~ 04-14）
- 新增日记：`2026-04-07` ~ `2026-04-14`（每日整理补录）
- 新增专项：`2026-04-09-category-report-comparison.md`、`2026-04-10-cbec-q1-sales-breakdown.md`
- 新增故障记录：`2026-04-13-whatsapp-gateway-reset.md`、`2026-04-04-session-issues.md`
- 新增每日资讯：`2026-04-13-daily-news-digest-2026-04-12.md`

### 2. Ontology 增量（本周）
| 日期 | 新增 Entities | 新增 Relations | 备注 |
|------|--------------|--------------|------|
| 04-08 | 少量（session 注册） | +34 | karpathy-pkm 重建后增量 |
| 04-11 | +50 sessions | +358 | 大规模历史补录 |
| 04-12 | +17 sessions | +17 | daily-cleanup 注册 |
| 04-13 | +30 sessions | +30 | 历史补录（部分被 cleanup 清理，净效果 0） |
| 04-14 | 0 | 0 | 幂等生效 |

### 3. 本周重要项目进展
- ✅ **karpathy-pkm SRC-0082 入库完成**：Swisse 2026.Q1 京东付费投放复盘（群邑电商）compiled_summary 已写入，当前 82 manifests / 215 concept pages
- ✅ **Swisse Q1 类目对比报告**：完整链路（飞书文档生成 → 评论通知 → Obsidian 补档）跑通；Gary 追加 CBEC 数据，发现肠胃益生菌口径差异并标注
- ✅ **AI Builders Digest 幂等 guard**：state-feed.json lastSentDate 检查，确认生效（04-13 daily-rollups 正常）
- ✅ **daily-rollups/2026-04-13.md 成功生成**：rollup cron 死锁问题短暂缓解（待根本修复）
- ✅ **Obsidian 派样人群复购分析**（04-13 晚）：Gary 讨论用 Obsidian 作为分析层+结论层，建议建 4 类笔记模板（项目总览/每次派样活动/复购结果/分群洞察）；关联 OPPO 抖音营销会议笔记

### 4. 系统稳定性（持续向好）
- **晨间 cron 稳定**：current session cron 机制 04-10 ~ 04-14 持续稳定，isolated session 网络故障未再触发
- **Cron 迁移完成**：19个 cron 从 isolated → current session，Gary 04-09 手动触发，效果确认

---

## 二、清理了什么

| 类型 | 数量 | 说明 |
|------|------|------|
| phantom session entities | 17个 | 04-12 清理：`session_sessions_*` 错误前缀，来自 memory-daily-cleanup 错误 agent_id |
| orphan relations | 17条 | 04-12 清理：phantom sessions 产生的孤儿关系 |
| sequential orphan relations | 41条 | 04-11 清理：重排序 graph.jsonl 消除 |
| duplicate SummaryNote | 1个 | 04-12 清理 |
| duplicate project entity | 1个 | `proj_karpathy_pkm` → 合并到 `project_karpathy_pkm` |
| phantom session creates | 多批 | 04-13 格式标准化，redirect 到 dash UUID canonical |

---

## 三、待补盲区（未闭环）

### 🔴 高优先级
1. **ISV 目录入库（部分完成）**
   - 路径：`/Users/garytan/Documents/garytan/宇先生/Documents/ISV`
   - SRC-0082（Swisse Q1 JD）已完成；剩余文件待继续 ingest
   - 阻塞：Gary 的 ISV 分析需求（04-13 Gary 要求查看「ISV 常用分析 Topic 库 0319」的17个项）

2. **Session entity ID 格式不一致（历史遗留）**
   - **现状**：graph 中 132 个 session entity 用纯下划线格式（如 `session_dev_09af70d8_40a4_...`），4 个用 dash+underscore 混合格式（canonical），而**实际文件系统**用纯 dash 格式（如 `09af70d8-40a4-425f-...jsonl`）
   - **影响**：memory-daily-cleanup 用 underscore 格式注册，daily-memory-refresh 用 dash 格式检查 → 同批 session 被反复重复注册/误清理
   - **修复方案**：统一 session entity ID = `session_{agent}_{session_filename_without_ext}`，session_filename 保持原样（含 dash），不要再做 dash→underscore 替换

3. **daily-rollup cron 死锁（持续性故障）**
   - 根因：全 Agent 日记 cron 依赖 rollup 文件存在，但 rollup cron 失败时形成等待链
   - 04-13 rollup 成功生成，但问题未根本解决，下次仍可能触发死锁
   - **修复方案**：cron payload 中加"rollup 不存在则自行汇总"兜底逻辑，不要等 rollup

### 🟡 中优先级
4. **ISV Daily Sync 中文路径编码问题**
   - 路径：`/Users/garytan/Documents/garytan/宇先生/Documents/ISV`
   - exec 调用时被错误编码，中文目录名失效
   - 持续时间：04-11 起

5. **Cron 调度器短时间重复触发**
   - daily-memory-refresh、AI Builders Digest 在 15~30min 内多次触发
   - 04-11~04-13 持续，调度器层面根因未解
   - 当前缓解：幂等 guard（state-feed.json）有效，但未根治

6. **飞书消息重复入队（04-02 历史）**
   - 主会话被 300+ 重复消息淹没，根因待查

---

## 四、本周新发现的重要规则（→ 补录到长期记忆）

### Rule: session entity ID 命名规范
> **命名格式**：`session_{agent_id}_{session_filename_without_ext}`  
> **filename 保持原始格式**（含 dash，不要替换为 underscore）  
> **注册源**：所有 session 注册统一由 daily-memory-refresh 执行，其他 cron 不要重复注册  
> **验证**：注册后查 graph.jsonl 确认无 orphan has_session relations  

### Rule: Idempotency Guard for Cron Jobs
> cron job payload 应在执行前检查 state-feed.json（或 equivalent）的 lastSentDate，相同 CST 日期已执行则跳过，避免重复触发浪费资源

### Project: Obsidian 分析层应用（04-13 Gary 新需求）
> Gary 将 Obsidian 用于"分析层 + 结论层"：原始数据在表格/SQL/多维表格，分析框架、实验记录、结论复盘、策略迭代在 Obsidian  
> 建议 4 类笔记模板：项目总览 / 每次派样活动 / 复购结果 / 分群洞察  
> 关联：OPPO 抖音营销会议笔记

### Project: ISV 常用分析 Topic 库（04-13 Gary 需求）
> Gary 要求整合 Obsidian「ISV 常用分析 Topic 库 0319」中17个项的所有具体 markdown → 飞书文档  
> **状态**：需求已提出，尚未执行

---

## 五、Ontology 一致性验证（04-14）

| 检查项 | 结果 |
|--------|------|
| Entity ID 唯一性 | ✅ 270 entities，无重复 |
| Orphan relations | ✅ 0 orphans |
| has_session 关系完整性 | ✅ 全部指向存在的 entity |
| Schema 类型一致性 | ✅ 无 type error |
| **⚠️ Session ID 格式** | ⚠️ 132 个 legacy underscore 格式（见上方待修复） |

---

## 六、WARM/MEMORY/HOT 更新计划

| 目标 | 动作 |
|------|------|
| WARM_MEMORY.md | 追加"本周新增规则"区块（Rule: session ID naming、Rule: Idempotency Guard、Project: Obsidian 分析层） |
| HOT_MEMORY.md | 追加 ISV Topic 库待办（高优先级）、Session ID 格式修复（中优先级） |
| MEMORY.md | 修复 Gary 偏好重复条目（已处理 ✅） |
| ontology | 暂无新 Project/Timeline/System entity；等待 ISV ingest 和 Obsidian 整合完成后补录 |

---

*下次每周整理：2026-04-21（周一）*
