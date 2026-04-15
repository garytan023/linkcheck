# 每周整理 | 2026-04-15（第15周）

> 整理时间：2026-04-15 06:08 AM CST
> 覆盖周期：2026-04-08 ~ 2026-04-15
> 撰写者：小拉（主会话 weekly-memory-review cron）

---

## 一、本周新增了什么

### 1. 记忆文件增量（04-08 ~ 04-15）
- 新增日记：`2026-04-08`、`2026-04-09`、`2026-04-13`、`2026-04-14`、`2026-04-15`
- 新增专项：`2026-04-13-1108.md`（WhatsApp gateway 测试会话）、`2026-04-13-whatsapp-gateway-reset.md`
- 新增周回顾：`weekly_review_2026-04-11.md` ~ `weekly_review_2026-04-14.md`（每日 cron 触发的短版报告）

### 2. Ontology 增量（本周）
| 日期 | 新增 Entities | 新增 Relations | 备注 |
|------|--------------|--------------|------|
| 04-12 | +30 sessions | +30 | 历史 session 补录 |
| 04-15 | +29 sessions | +29 | 04-12~04-15 新批次 |

**当前 ontology**：296 entities / 963 relations / **0 orphans** ✅

### 3. 本周重要项目进展

#### ✅ karpathy-pkm 引用策略切换（04-15 凌晨）
- `obsidian_doc_sync_to_kk.py` 不再复制正文到 raw/sources
- 改为生成 reference stub，记录 `source_path` / `obsidian://` 路径
- 新增 `kk_reference_source_backfill.py`（历史 manifest 回填 + stub 生成）
- 新增 `kk_reference_compile_prep.py`（按 manifest 回读原文，生成 compile queue）
- **未闭环**：最后一步"把 compile 结果写回 manifest.compiled_summary 并更新 wiki"仍需手动
- Git commits: `89e7300`、`284c330`

#### ✅ 所有 Agent 日记 cron 本周全部正常（04-11~04-15）
- 22:00~23:35 批次（小风/小数/小投/小创/小码/小诊/小知）全部 ok
- 小风/小诊历史 consecutive timeout 已清零
- 全 Agent 中间汇总层（22:50）稳定生成

#### ✅ daily-rollup 本周持续生成
- 2026-04-11.md ~ 2026-04-14.md 全部成功
- 04-09 rollup 目录存在但内容为空（历史问题，未再触发）

#### ✅ AI Builders Digest 幂等 guard 持续有效
- `state-feed.json` lastSentDate 检查确认生效
- 04-11~04-15 无重复发送报告

#### ✅ Swisse Q1 工作流完成
- CBEC 数据已追加（跨境自营 24个三级类目 + 大贸自营 21个三级类目）
- 口径差异已标注（肠胃益生菌小计 vs 上级汇总）
- ⚠️ Present 前需 Gary 提供原始 Excel 核对

#### 🔴 ISV 常用分析 Topic 库 0319 → 飞书文档（**未执行**）
- Gary 04-13 19:09 明确要求：整合17个分析项的所有 markdown → 飞书文档
- **状态：需求已接收，待执行**，高优先级

#### 🔴 karpathy-pkm reference compile runner（**未闭环**）
- reference queue 已能生成，但尚未自动写回 manifest / wiki
- 需补最后一个自动化步骤

---

## 二、清理了什么

| 类型 | 数量 | 说明 |
|------|------|------|
| 错误路径 session entity | 5个 | tilde 路径（`~/.openclaw/...`）→ 绝对路径 |
| 错误 agent_id 格式 | 多个 | `agent_dev` → `dev` 等标准化 |
| consecutive timeout 清零 | 2个 | 小风/小诊日记 cron 历史 timeout 全部清零 |

---

## 三、跨 Agent / 跨账号重要线索

### Agent 账号分布（截至 04-15）
| Agent | 飞书账号 | 用途 | 状态 |
|-------|---------|------|------|
| dev（小拉风）| xiaofeng | 统筹/主控/记忆系统 | 持续活跃 |
| assistant（拉大风）| xiaofeng | 辅助会话/follow-builders | 活跃 |
| la_xiao_zhi | xiaofeng | 资讯/知识库 | cron 活跃 |
| la_xiao_shu | xiaofeng | 数据分析 | cron 活跃 |
| la_xiao_tou | xiaofeng | 媒介投放 | cron 活跃 |
| la_xiao_chuang | xiaofeng | 创意设计师 | cron 活跃 |
| la_xiao_zhen | xiaofeng | 素材诊断 | cron 活跃 |
| la_xiao_ma | xiaofeng | 程序员 | cron 活跃 |

### Gary Obsidian 定位更新（04-13 晚）
- **分析层 + 结论层**：原始数据在表格/SQL/多维表格；分析框架、实验记录、结论复盘、策略迭代在 Obsidian
- **建议4类笔记模板**：项目总览 / 每次派样活动 / 复购结果 / 分群洞察
- **关联**：OPPO 抖音营销会议笔记

### Cron Job 健康状况（本周）
| Job | Session | consecutiveErrors | 本周状态 |
|-----|---------|-------------------|---------|
| 所有 Agent 日记（7个）| current | 0 | ✅ 全部正常 |
| 全Agent中间汇总层 | current | 0 | ✅ 正常 |
| ISV Daily Sync | current | 0 | ✅ 正常 |
| ISV每日入库+Feishu通知 | current | 0 | ✅ 正常 |
| 每日资讯精选 | current | 0 | ✅ 正常 |
| AI Builders Digest | isolated | 0 | ✅ 幂等 guard 有效 |
| memory-weekly-review | current | 0 | ✅ 正常 |
| memory-daily-cleanup | isolated | 1 | ⚠️ 偶发 timeout |
| Obsidian Inbox | isolated | 0 | ✅ 正常 |

---

## 四、Ontology 一致性验证（04-15）

| 检查项 | 结果 |
|--------|------|
| Entity ID 唯一性 | ✅ 296 entities，无重复 create |
| Orphan relations | ✅ 0 orphans |
| has_session 关系完整性 | ✅ 全部指向存在的 entity |
| Schema 类型一致性 | ✅ 无 type error |
| **⚠️ Session ID 格式** | ⚠️ 132 个 legacy underscore 格式（04-21 前修复，已拖延一周）|

### Entity 类型分布
Session(218) + SummaryNote(26) + Agent(14) + Rule(9) + Topic(9) + RoleTag(5) + PriorityTag(4) + Document(3) + Preference(2) + Project(2) + Account(2) + Person(1) + System(1)

### ⚠️ 规则/Tool 重复项（不阻塞，但需整理）
- **Rule `rule_isv_partial_ingestion_done`**：描述字段为空（name 也为空），疑似创建时漏填，不影响功能但影响可读性

---

## 五、补录到长期记忆的条目

| 条目 | 目标层 | 内容摘要 |
|------|--------|---------|
| karpathy-pkm reference-only 策略 | HOT + WARM | 04-15 切换，3个 helper 脚本已就绪，compile 最后一步待闭环 |
| Gary Obsidian 定位 | WARM | 分析层+结论层，4类笔记模板建议 |
| ISV Topic 库 0319 需求 | HOT + WARM | Gary 04-13 晚明确需求，待执行 |
| Agent 日记 cron 全部正常 | HOT + WARM | 小风/小诊历史 timeout 清零，当前 0 errors |
| 重复 cron job 问题 | HOT + WARM | `memory-weekly-review` vs `weekly-memory-review` 两套并行，建议合并 |
| memory-daily-cleanup isolated 偶发 timeout | HOT | consecutiveErrors=1，建议改为 current session |

---

## 六、还有哪些待补盲区

### 🔴 高优先级（必须处理）
1. **ISV Topic 库 0319 → 飞书文档**：Gary 04-13 晚明确需求，**待执行**
2. **karpathy-pkm reference compile runner**：queue 已能生成，但最后一步未自动化
3. **Session entity ID 格式修复**：132 个 legacy underscore 格式，**04-21 前（已拖延一周）**
4. **重复 cron job 合并**：`memory-weekly-review` vs `weekly-memory-review` 并行，建议禁用后者保留 python-script 版本

### 🟡 中优先级
5. **daily-rollup cron 死锁根因**：04-09~04-15 持续，rollup 不存在时各 cron 应自行兜底（已建议但未根本修复）
6. **ISV Daily Sync 中文路径编码**：`宇先生/Documents/ISV` exec 编码问题，04-11 起持续
7. **memory-daily-cleanup 改为 current session**：isolated 偶发 timeout

### 🟢 低优先级
8. **Cron 调度器重复触发根因**：幂等 guard 缓解，调度器层面待查
9. **Rule `rule_isv_partial_ingestion_done` 描述字段为空**：可读性问题，不影响功能
10. **Swisse Q1 口径差异**：肠胃益生菌小计不符，Present 前需 Gary 原始 Excel 核对

---

*下次每周整理：2026-04-22（周三）*
