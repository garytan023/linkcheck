# 学习日志

> 记录错误、修正和最佳实践

## 使用说明

当发生以下情况时，记录到本文件：

- 用户纠正了你的回答（类别：`correction`）
- 发现知识过期或不准确（类别：`knowledge_gap`）
- 找到更好的解决方案（类别：`best_practice`）
- 工作流改进（类别：`workflow`）

## 格式

```markdown
## [LRN-日期-序号] category

**Logged**: 时间
**Priority**: low | medium | high | critical

### Summary
一句话描述

### Details
详细上下文
```

---

## 本周学习

### [LRN-20260306-01] workflow

**Priority**: high

### Summary
定时任务发送失败后需要验证送达

### Details
- 问题：定时任务执行后未确认消息是否真正送达 Discord 频道
- 解决：添加 `message read` 验证步骤
- 改进：更新 AGENTS.md 记录此流程
