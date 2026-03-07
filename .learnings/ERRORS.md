# 错误日志

> 记录命令失败、异常和 API 错误

## 使用说明

当发生以下情况时，记录到本文件：

- 命令/操作失败
- 外部 API 调用失败
- 工具异常

## 格式

```markdown
## [ERR-日期-序号]

**Logged**: 时间
**Severity**: low | medium | high | critical

### Error
错误信息

### Context
发生场景

### Fix
解决方案
```

---

## 本周错误

### [ERR-20260306-01] GitHub push 被拒绝

**Severity**: medium

### Error
```
! [rejected] main -> main (fetch first)
error: failed to push some refs
```

### Context
推送到 garytan023/linkcheck 时，远程已有内容

### Fix
选择 "强制推送" 或 "先 pull 合并"

---

### [ERR-20260306-02] 飞书文档写入长度限制

**Severity**: medium

### Error
内容被截断，无法一次性写入完整文档

### Context
使用 `update_block` 写入大量内容时

### Fix
分段写入或简化内容

---

### [ERR-20260306-03] 飞书云盘权限不足

**Severity**: medium

### Error
403/400 错误，权限不足

### Context
调用 `feishu_drive` 创建文件夹或移动文件

### Fix
在飞书开放平台申请 `drive:file` 等权限并发布新版本
