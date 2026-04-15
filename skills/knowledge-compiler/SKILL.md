---
name: knowledge-compiler
description: "LLM 驱动的个人知识编译系统。核心理念：不要每次用时从零 RAG，而是把原始来源增量编译成结构化互链 wiki。触发词：'kk'、'知识编译'、'kk init'、'kk ingest'、'kk compile'、'kk ask'、'kk maintain'、'kk promote'、'kk link'、'kk help'、'研究知识库'、'编译 wiki'、'来源管理'。"
---

# Knowledge Compiler (kk)

LLM 驱动的个人知识编译系统。核心理念：把原始来源**增量编译**成结构化互链 wiki，而不是每次从零检索。

## 架构定位

本 skill 运行在 OpenClaw × Obsidian 体系之上，不另起炉灶：

| kk 层 | 映射到我们现有体系 |
|-------|-----------------|
| `raw/` | `Inbox/`（用户投入的原始来源）|
| `wiki/` | `知识库/`（编译后的结构化页面）|
| `outputs/` | `临时产出/`（ask/maintain 的结果）|
| `curated/` | 手动认可后手动归档 |

**我们的改进**：raw/sources 直接复用 Obsidian vault 的 `Inbox/` 目录，不另建隔离层。来源通过 manifest 追踪。

## 硬规则

1. `raw/` 永远是权威来源，只读
2. `wiki/` 是派生层，可从 raw 重建
3. `outputs/` 默认不可信，只是任务结果
4. `curated/` 是最终认可层
5. **所有非平凡断言必须可回链到 source manifest**
6. `log.md` 是 append-only，脚本自动写入，LLM 禁止手动修改
7. 无来源的推测内容用 `[TODO: 待验证]` 标注，禁止无据填充

## 决策树

| 用户意图 | 路由 |
|:---|:---|
| "kk help" / "命令列表" | → **help** |
| "kk init X" / "建一个研究库" | → **init** |
| "kk ingest" / "收录这篇" / "把这个文件加进来" | → **ingest** |
| "kk compile" / "编译一下" / "更新 wiki" | → **compile** |
| 直接提研究问题 | → **ask** |
| "kk maintain" / "检查知识库" / "有什么遗漏" | → **maintain** |
| "kk promote" / "晋升" / "推到主库" | → **promote** |
| "kk link" / "关联主库" / "搜索相关笔记" | → **link** |

## 工作区路径约定

**base**: `/Users/garytan/Documents/garytan/知识库/`

每个研究项目是一个子目录，结构：

```
<project-name>/
  AGENTS.md              ← schema 契约
  log.md                 ← append-only 操作日志
  inbox/                 ← 原始来源入口（对应 raw/inbox）
  sources/               ← 已登记来源副本（对应 raw/sources）
  manifests/
    sources/             ← 每个来源一个 SRC-NNNN.json
    source_index.csv     ← 来源汇总索引
  wiki/
    indexes/
      master_index.md    ← 主索引
    concepts/             ← 概念页
    entities/             ← 实体页
    themes/              ← 主题综述页
  outputs/
    answers/             ← ask 回答
    reports/             ← 综合报告
  maintain/
    findings/            ← 巡检发现
    gaps/                ← 知识缺口
  curated/
    promoted/            ← 经认可的产物
```

## 命令

### help

直接输出（不需要脚本）：

| 命令 | 说明 |
|------|------|
| `kk init <name>` | 新建研究 workspace |
| `kk ingest <path>` | 收录文件/文件夹到研究库 |
| `kk compile` | 增量编译 wiki |
| `kk compile --full` | 全量重编译 |
| `kk ask "<问题>"` | 基于 wiki 回答研究问题 |
| `kk maintain` | 巡检 wiki 质量 |
| `kk promote <path>` | 晋升产物到 curated |
| `kk link --detail` | 检索 wiki 实体在主库的关联 |
| `kk link seed --topic "<词>"` | 从主库拉取相关笔记到 inbox |
| `kk status` | 显示当前 workspace 状态 |

---

### init `<project-name>`

```bash
python3 scripts/kk_init.py <project-name>
```

- 在 `/Users/garytan/Documents/garytan/知识库/<project-name>/` 创建完整目录结构
- 生成 `AGENTS.md`
- 设为"当前活跃 workspace"（写入 `.active_workspace` 文件）
- 自动创建 `log.md`、`source_index.csv`、空的 wiki 索引

---

### ingest `<path>`

```bash
python3 scripts/kk_ingest.py <workspace-path> <source-path>
python3 scripts/kk_ingest.py <workspace-path> --inbox
```

- 复制原文件到 `sources/`
- 生成 source manifest（SRC-NNNN.json）
- 更新 `source_index.csv`
- 支持类型：`.md`、`.txt`、`.pdf`、`.html`
- 自动 SHA-256 去重
- `--inbox`：处理 inbox 目录所有文件

**ingest 后**：LLM 必须为每个新来源生成一句话摘要并写入 manifest 的 `summary` 字段（直接编辑 JSON）。

---

### compile [--full]

```bash
python3 scripts/kk_compile.py <workspace-path> [--full]
```

**两阶段**：
1. **Per-source pass**：读每个未编译的来源 → LLM 提取概念/实体/关键论点 → 写入 manifest 的 `compiled_summary`
2. **Cross-source pass**：读所有摘要 → LLM 生成/更新 wiki 页面 → 补 backlinks → 更新 `master_index.md`

**增量逻辑**：默认只处理 `compiled_summary == null` 的来源；`--full` 重建全部。

---

### ask `"<question>"` [--format md|marp]

基于 wiki 回答研究问题。

1. 读 `wiki/indexes/master_index.md` 定位相关页面
2. 读相关 wiki 页面（必要时回读 sources 验证）
3. 生成回答，写入 `outputs/answers/YYYY-MM-DD_<slug>.md`
4. **wiki 回灌**：检查回答是否有新概念/洞察，如有则更新相关 wiki 页面（标注 `(ASK-YYYY-MM-DD)`）
5. 记录到 `log.md`

---

### maintain [--full]

```bash
python3 scripts/kk_maintain.py <workspace-path> [--full]
```

- quick：断链、无来源断言、缺失字段
- `--full`：+ 重复概念合并建议、新文章候选、知识缺口

产出写入 `maintain/findings/` 或 `maintain/gaps/`。

---

### promote `<path>`

```bash
python3 scripts/kk_promote.py <workspace-path> <artifact-path>
```

- 检查来源完整性 + 信息密度
- 移动到 `curated/promoted/`
- 可手动进一步推到 Obsidian 主库（`宇先生/` 下的对应目录）

---

### link [--detail] [seed --topic `"<词>"`]

- `--detail`：输出 wiki 所有概念/实体在主库 `宇先生/` 中的命中情况
- `seed --topic "<词>"`：在 `宇先生/` 知识库中搜索相关笔记，复制到当前 workspace 的 `inbox/`

---

### status

```bash
python3 scripts/kk_status.py <workspace-path>
```

输出：workspace 名称、来源数、wiki 页数、outputs 数、待编译数。

## 命名规范

- 来源文件名：保留原始，放入 `sources/`
- Manifest：`SRC-NNNN.json`（如 `SRC-0001.json`）
- Wiki 页面：`kebab-case.md`（如 `transformer-architecture.md`）
- Outputs：`YYYY-MM-DD_<slug>.md`

## 来源溯源格式

Wiki 页面头部标注来源：

```markdown
> 来源: [[SRC-0001]], [[SRC-0003]]

## 定义

内容 (SRC-0001)

> [!warning] 未验证
> 此处为推测，待补充来源
```

## Source Manifest Schema

路径：`manifests/sources/SRC-NNNN.json`

```json
{
  "id": "SRC-NNNN",
  "title": "来源标题",
  "type": "article|paper|book|video|tweet|other",
  "source_url": "原始 URL 或 null",
  "date_ingested": "YYYY-MM-DD",
  "date_published": "YYYY-MM-DD 或 null",
  "file_path": "sources/filename.md",
  "content_hash": "SHA-256",
  "summary": "一句话摘要（ingest 时生成）",
  "compiled_summary": null,
  "concepts": [],
  "entities": [],
  "tags": []
}
```
