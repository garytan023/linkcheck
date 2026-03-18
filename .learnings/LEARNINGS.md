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

### [LRN-20260310-01] workflow

**Priority**: high

### Summary
飞书文档权限API修复：从Python REST API多次失败，最终用Node.js SDK成功

### Details
- 问题：创建飞书文档后无法自动开放full_access权限给用户
- 尝试：permission/v3/member_permissions (404) → drive/v3/permission_members (404) → token前缀docx_ (404) → ACL API (404)
- 最终解决：使用Node.js SDK调用 `client.drive.permissionMember.create()` 成功
- 改进：创建 add_perm.sh 脚本，通过 subprocess 调用 Node.js 设置权限

### [LRN-20260318-01] workflow

**Priority**: high

### Summary
Heartbeat 不能机械回复 HEARTBEAT_OK，必须先核验当天必做任务是否真的执行

### Details
- 问题：明明 HEARTBEAT.md 里写了早间复盘、9点资讯同步、晚间日记、记忆清理等硬要求，却出现了直接回 `HEARTBEAT_OK` 的情况
- 影响：会把“未执行”伪装成“无事发生”，尤其容易漏掉定时任务失败、文件没落盘、通知没送达
- 正确做法：先检查文件、cron 运行结果、目标产物是否存在；确认无待处理事项后，才允许回复 `HEARTBEAT_OK`
- 改进：以后把 heartbeat 当巡检，不当自动点名应答
