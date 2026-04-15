# 每周记忆回顾报告 | 2026-04-13

> 时间范围：2026-04-06 ~ 2026-04-13
> 整理时间：2026-04-13 07:11 AM (Asia/Shanghai)
> 整理依据：memory/ 日记（04-06~04-13）+ ontology graph + WARM/HOT/MEMORY.md

---

## 一、本周新增了什么

### 1. Ontology 大清理（最大事件）
- **20个 phantom session entity 清除**：
  - 来源：历史遗留，同一 session UUID 的 dash 格式和 underscore 格式被分别注册为两个 entity
  - Dash 格式（`session_assistant_23a0d3f2-0dde-4565-...`）= canonical（对应真实 session 文件名）
  - Underscore 格式（`session_assistant_23a0d3f2_0dde_4565_...`）= phantom
  - Phantom entity 删除：20条 `create` 记录
  - Phantom relations 修复：79条 `relate` 记录 redirect 到 canonical entity
- **清理后**：270 entities / 937 relations / **0 orphans** ✅
- 04-12 遗留 phantom `session_sessions_*` bug（17个）之后，本周进一步解决了 dash/underscore UUID 混用问题

### 2. 系统稳定性持续验证
- **current session cron 机制稳定**：04-10~04-13 连续4天晨间 cron 全部正常，isolated session 网络故障问题未再触发
- **19个 cron 从 isolated → current session 迁移完成**（04-09 Gary 手动）：效果确认有效

### 3. karpathy-pkm ISV 入库完成（04-09~04-10）
- **SRC-0082（Swisse 2026.Q1 京东付费投放复盘，群邑电商）入库完成**
- 当前：82 manifests，215 concept pages
- ISV 目录剩余文件仍待后续 ingest

### 4. Swisse Q1 工作流深化（04-10凌晨）
- Gary 追加 CBEC 自营/大贸自营数据（跨境自营 24个三级类目 + 大贸自营 21个三级类目）
- **⚠️ 数据口径差异**：肠胃益生菌小计与上级汇总不符；Present 前需 Gary 提供原始 Excel 核对
- 完整链路跑通：图片 → 飞书文档（含表格）→ CBEC数据 → Obsidian 补档

### 5. Cron 重复触发问题确认（系统性）
- **04-11~04-13 持续**：daily-memory-refresh、AI Builders Digest 在短时间（<30min）内多次触发
- 04-12 22:01~22:06 期间多 cron 同时出现 dup，间隔 <10min
- **建议方案**：cron payload 加幂等 guard — 发送前查 `state-feed.json` 的 lastSentDate，若今天(CST)已发过则跳过
- **⚠️ 状态**：方案已提出（04-11），实施状态待 Gary 确认

### 6. AI Builders Digest 活跃
- Gary feishu 群聊关注：Sam Altman $100 Pro 档、levie 非结构化数据观点、karpathy 认知鸿沟文
- 04-13 dafeng 线活跃（Swisse Q1 需求处理）

---

## 二、清理了什么

### 1. Ontology 一致性
- ✅ 20个 phantom session entities 删除（DASH/UNDERSCORE UUID 混用）
- ✅ 79条 phantom relations 全部 redirect 到 canonical entity
- ✅ 0 orphans remaining
- ✅ Entity type breakdown: Session(192) + SummaryNote(26) + Agent(14) + Rule(9) + Topic(9) + PriorityTag(4) + Document(3) + Account(2) + Preference(2) + Project(2) + RoleTag(5) + Person(1) + System(1)

### 2. 三层记忆归并
- **HOT_MEMORY.md**：更新最后时间，追加04-13 Ontology 状态，标记 ISV Daily Sync 中文路径编码问题为高优
- **WARM_MEMORY.md**：追加4条新规则（session UUID 标准化、AI Builders Digest 幂等方案、Cron 重复触发系统性观察、dafeng 线活跃）
- **MEMORY.md**：追加04-12~04-13 每周整理条目

---

## 三、跨 Agent / 跨账号重要线索

### Agent 账号分布（截至 04-13）
| Agent | 飞书账号 | 用途 | 状态 |
|-------|---------|------|------|
| dev（小拉风）| xiaofeng | 统筹/主控/记忆系统 | 持续活跃 |
| dafeng（assistant）| xiaofeng/dafeng | 辅助会话/跨账号 | 04-10 活跃 |
| la_xiao_zhi | xiaofeng | 资讯/知识库 | 活跃 |
| la_xiao_shu | xiaofeng | 数据分析 | 活跃 |
| la_xiao_tou | xiaofeng | 媒介投放 | 活跃 |
| la_xiao_chuang | xiaofeng | 创意设计师 | 活跃 |
| la_xiao_zhen | xiaofeng | 素材诊断 | 活跃 |
| la_xiao_ma | xiaofeng | 程序员 | 活跃 |

### 关键项目线索
- **karpathy-pkm**：ISV 部分入库（SRC-0082完成）；剩余文件待继续 ingest； ontology entity: `project_karpathy_pkm`
- **Swisse Q1 工作流**：图片→飞书文档→CBEC数据→Obsidian 补档，完整链路跑通；⚠️数据口径问题待 Gary 原始 Excel 核实
- **cron 稳定性**：isolated session 依赖已移除（04-09）；current session cron 机制稳定（04-10~04-13）
- **记忆系统**：Ontology session entity paired design 确认正确（DASH/UNDERSCORE UUID 混用历史 bug 已标准化）

---

## 四、补录到长期记忆的条目

| 条目 | 目标层 | 内容摘要 |
|------|--------|---------|
| session entity ID 格式标准化 | WARM | Dash UUID = canonical；Underscore = phantom；79条 relations 已 redirect |
| AI Builders Digest 幂等方案 | WARM/HOT | state-feed.json lastSentDate guard；方案已提出，实施待确认 |
| Cron 重复触发系统性观察 | WARM/HOT | 同一调度周期内多次触发，<10min 间隔；调度器问题待查 |
| dafeng 线活跃 | WARM | 04-10 Swisse Q1 需求处理；Gary 关注 AI 动态 |
| Ontology 当前状态 | HOT | 270 entities / 937 relations / 0 orphans（04-13 验证） |

---

## 五、待补盲区（需 Gary 确认）

1. **【高优】AI Builders Digest 幂等 guard 是否已实施？** 方案已在04-11提出，dafeng/assistant 线待 Gary 确认实施状态
2. **【高优】ISV 目录剩余文件 ingest 计划**：`/Users/garytan/Documents/garytan/宇先生/Documents/ISV` 还有未入库文件
3. **【高优】ISV Daily Sync 中文路径编码问题**：`宇先生/Documents/ISV` 在 exec 调用时被错误编码（04-11 起持续）
4. **【中优】daily-rollup cron 死锁**：rollup 不存在时 cron 应自行兜底（04-09~04-13 持续，根因未修复）
5. **【中优】Swisse Q1 数据口径差异**：肠胃益生菌小计不符；Present 前需 Gary 提供原始 Excel 核对
6. **【低优】Cron 调度器重复触发根因**：调度器本身的问题，需进一步排查

---

## 六、Cron 运行时观察（补充）

### 本周 cron 异常汇总
| Job | Session | consecutiveErrors | lastErrorReason |
|-----|---------|-------------------|----------------|
| ISV每日入库 + Feishu通知 | isolated | **5** | timeout (155s) |
| AI Builders Digest | isolated | 0 | — |
| 小诊每日日记 | current | **5** | timeout |
| 小风每日日记 | current | **8** | timeout |

**分析**：
- **ISV每日入库**（isolated，5次timeout）：ISV 同步 job 也跑 isolated session，但 karpathy-pkm 入库流程包含 MiniMax LLM call，可能在 isolated 环境下超时。建议改为 current session（已有一个同功能 cron "ISV Daily Sync to karpathy-pkm" 是 current，正常）
- **小风每日日记**（current，8次timeout）：持续 timeout 说明 payload 依赖某项资源不可用；很可能是 daily-rollup 文件依赖（rollup 不存在时自己无法兜底）
- **小诊每日日记**（current，5次timeout）：同上

### 建议 Gary 手动处理
1. 将 AI Builders Digest 从 `isolated` → `current` session（避免晨间网络故障影响）
2. 删除或禁用重复的 ISV每日入库 cron（已有 current session 版本正常工作）
3. 修复 ISV Daily Sync 中文路径编码问题（宇先生路径 exec 编码问题）

