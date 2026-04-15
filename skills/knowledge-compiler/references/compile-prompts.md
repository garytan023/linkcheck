# Compile Prompts — 来源编译模板

## Per-Source Pass

读来源文件，输出 JSON：

```json
{
  "summary": "一句话摘要",
  "concepts": ["概念A", "概念B"],
  "entities": ["实体X", "实体Y"],
  "key_claims": [
    {
      "claim": "核心断言内容",
      "evidence": "支撑证据摘要"
    }
  ],
  "tags": ["标签1", "标签2"],
  "word_count": 150
}
```

## Wiki Page Generation Prompts

### 概念页 (concepts/)

读来源摘要后生成：

```markdown
# <概念名>

> 来源: [[SRC-NNNN]], [[SRC-MMMM]]

## 定义

[概念定义，标注来源]

## 关键论点

- 论点1 (SRC-NNNN)
- 论点2 (SRC-MMMM)

## 相关概念

- [[related-concept]]
- [[another-concept]]

## 开放问题

- [TODO: 待验证...]
```

### 实体页 (entities/)

```markdown
# <实体名>

> 来源: [[SRC-NNNN]]

## 基本信息

[实体关键事实]

## 主要观点/贡献

- ... (SRC-NNNN)

## 相关实体

- [[entity-x]]
- [[entity-y]]
```

### 主题综述页 (themes/)

```markdown
# <主题名>

> 综合来源: [[SRC-0001]], [[SRC-0002]], [[SRC-0003]]

## 概览

[综合多个来源的主题综述，标注各来源贡献]

## 争议与分歧

- ... (SRC-0001 vs SRC-0002)

## 知识缺口

- [TODO: ...]
```

## 来源类型路由

| 类型 | 处理策略 |
|------|---------|
| `article` | 提取核心论点、概念、实体 |
| `paper` | 重点：方法、贡献、局限性 |
| `video` | 提取：要点列表、关键洞察、时间标记 |
| `book` | 章节摘要、核心框架、引用 |
| `tweet` | 观点提取、关联实体 |
| `other` | 通用摘要处理 |

## 溯源标注规范

- Wiki 页面头部 blockquote 列出所有来源
- 每个非平凡断言行尾标注来源ID：` (SRC-NNNN)`
- 无来源推测用 callout：`> [!warning] 未验证`
- 知识缺口用 `[TODO: 待补充来源]`
