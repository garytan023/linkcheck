# 每周记忆回顾报告 | 2026-04-10

> 时间范围：2026-04-03 ~ 2026-04-10
> 整理时间：2026-04-10 06:15 AM (Asia/Shanghai)
> 整理依据：memory/ 日记（04-03~04-10）+ ontology + WARM/HOT/MEMORY.md

---

## 一、本周新增了什么

### 1. 知识库里程碑
- **karpathy-pkm ISV SRC-0082 入库完成**（04-09）：Swisse 2026.Q1 京东付费投放复盘（群邑电商），compiled_summary 写入完成
- **最终规模**：82 manifests，215 concept pages
- ISV 目录剩余文件（`/Users/garytan/Documents/garytan/宇先生/Documents/ISV`）仍未全量入库，阻塞 Gary 需求

### 2. Gary 工作流跑通（04-09 晚）
- Swisse Q1 类目对比报告：图片 → 飞书文档（含完整表格）→ Obsidian 归档
- 完整链路：Gary 发图 → 小拉生成飞书文档 → 评论通知 → Obsidian 补档
- ontology 已记录：`doc_swisse_q1_feishu`

### 3. 系统稳定性修复
- **19个 cron 从 isolated → current session 迁移**（Gary 手动，04-09）：减少 isolated session 依赖
- **04-04 模型修复结论落地**：MiniMax-Text-01 替换 M2.7-highspeed，5个 sub-agent 日记恢复正常
- **04-08 ontology 修复**：77处 `assitant`→`assistant` 拼写错误，+34 sessions 入库

### 4. 新增规则（ontology 补录）
| Rule ID | 标题 | 时间 |
|---------|------|------|
| rule_gary_ok_only | Gary 直接消息 → 简短"ok"确认 | 04-03 |
| rule_xhs_video_pipeline | 小红书视频处理链路 | 04-06 |
| rule_cron_no_circular_deps | cron 无前置依赖兜底原则 | 04-08 |
| rule_cron_morning_network | 晨间 isolated cron 网络全灭 | 04-09 |
| rule_cron_migration_done | 19个 cron 已迁至 current | 04-09 |

---

## 二、清理了什么

### 1. ontology duplicate entity merge
- **问题**：`project_karpathy_pkm`（04-08 创建）和 `proj_karpathy_pkm`（04-09 创建）指向同一实体，描述不一致（前者"ISV目录待入库"，后者"82 manifests/215 concept pages"）
- **处理**：保留 `proj_karpathy_pkm`（更新更完整），追加3条 redirect relations 使 `project_karpathy_pkm` 指向 `proj_karpathy_pkm`
- **结果**：665 → 668 lines，190 entities，0 orphans

### 2. memory 补档
- **2026-04-09.md 缺失**：daily-rollup 目录为空导致 agent 日记全部断档，本次补录 `memory/2026-04-09.md`（含 SRC-0082、Swisse 报告、cron 全灭事件）

### 3. 重复标签清理（merge-first 原则）
- HOT_MEMORY.md 合并：本周完成项不再重复分散，已统一归档
- WARM_MEMORY.md：Gary 偏好规则去重（"拒绝废话"等条目已统一合并）

---

## 三、跨 Agent / 跨账号重要线索

### Agent 账号分布
| Agent | 飞书账号 | 主要功能 | 本周状态 |
|-------|---------|---------|---------|
| 小拉风（dev）| xiaofeng | 统筹/主控 | 持续活跃 |
| assistant（分身）| xiaofeng/dafeng | 辅助解释 | 少量 session |
| la_xiao_zhi | — | 资讯/知识库 | SRC-0082 编译完成 |
| la_xiao_shu | — | 数据分析 | 日记正常 |
| la_xiao_ma | — | 代码/自动化 | Obsidian Inbox 整理 |
| la_xiao_tou | — | 媒介投放 | 本周无独立 session |
| la_xiao_zhen | — | 诊断/审计 | 本周无独立 session |
| la_xiao_chuang | — | 创意设计 | 本周无独立 session |

### 关键发现
- **真正活跃的只有 dev 和 la_xiao_zhi/su/ma**：其余3个 agent（tou/zhen/chuang）本周无 session 产出，不是"全员协作"，是"主控+部分子 agent"
- **la_xiao_zhi/skills/ 目录为空软链接**：skills 目录存在但实际为软链接指向 `skills`，内容为空——这意味着 la_xiao_zhi 没有独立 skill 配置，依赖 workspace-dev/skills 主库
- **cron 稳定性改善**：19个迁移至 current session，但晨间 isolated cron 仍每天全灭（根因未解）

### 权限/配置信息（已确认）
- Gary openid: `ou_d635f4f3d20ac474cf8575038b5d2b33`
- dafeng openid: `ou_2b61cfc2e4c54c32e1734a48458b1d76`
- 飞书 APP: `cli_a9f1b6fb6b3bdbc2`
- karpathy-pkm vault: `/Users/garytan/Documents/garytan`
- Obsidian vault: `/Users/garytan/Documents/garytan`（CLI v1.12.7）
- 当前主 workspace: `/Users/garytan/.openclaw/workspace-dev`

---

## 四、待补盲区

| # | 盲区 | 优先级 | 阻塞 |
|---|------|--------|------|
| 1 | **晨间 cron 网络故障根因**（isolated session 06:00 AM 全灭，持续近2周） | 高 | Gary 无法收到晨间日报 |
| 2 | **ISV 目录剩余文件入库**（`/Users/garytan/Documents/garytan/宇先生/Documents/ISV`）| 高 | Gary 需求未完全闭环 |
| 3 | **la_xiao_tou/zhen/chuang 日记无产出**：是否有独立 cron 在跑？是否真的在执行？ | 中 | 不知道这些 agent 实际在干啥 |
| 4 | **RSS 代理**：04-07 全挂（45/45），04-09 状态不明，信息源头枯竭 | 中 | 每日资讯输入断连 |
| 5 | **飞书消息重复入队根因**：04-02 300+ 重复消息，尚未查清 | 中 | 主会话稳定性风险 |
| 6 | **daily-rollup 死锁**：rollup 为空导致所有 agent 日记无法正常生成 | 中 | 记忆系统持续断档 |
| 7 | **la_xiao_zhen/skills/dist** 目录仍疑似构建产物 | 低 | 空间/一致性风险 |

---

## 五、Ontology 一致性验证结果（2026-04-10）

```
Entities (create): 190
Relations (relate): 478
Total lines: 668
Duplicate entity IDs: 0
Orphan relations: 0 ✓
```
- **Merge done**: `project_karpathy_pkm` → `proj_karpathy_pkm`（+3 redirect relations）
- **Schema 校验**：12 entity types，10 relations，全部符合 schema.yaml
- **Next action**：下次周整理（04-17）前，需专项修复晨间 cron 网络根因

---

**下次周整理目标**：确认晨间 cron 根因是否修复；ISV 目录全量入库闭环；la_xiao_tou/zhen/chuang 实际运行状态确认
