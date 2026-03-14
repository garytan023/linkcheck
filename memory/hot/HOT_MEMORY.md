# HOT Memory - 当前任务

## 当前高优先级
- [ ] 修复记忆召回：memory_search embedding 配置异常（401 invalid_api_key）
- [ ] 降低失忆风险：把关键偏好与工作流固化到 USER/MEMORY/WARM
- [ ] 修正资讯同步流程：不只跑脚本，还要确保结果真正落到飞书文档并可访问

## 当前问题
- memory plugin 不是完全不可用，而是语义召回链路有故障
- lossless-claw 只负责上下文压缩，不负责替代长期文件记忆
- 飞书文档写入仍是两步：脚本创建 / 整理内容 → 文档工具写入 / 权限确认

## 当前操作原则
- 重要事实先落盘，再指望插件召回
- 回答“你还记得吗/之前怎么定的”这类问题时，优先查本地记忆与 LCM
- 没验证的流程不能宣称完成

## 今日重要信息
- 飞书 APP ID: cli_a9f1b6fb6b3bdbc2
- Gary openid: ou_d635f4f3d20ac474cf8575038b5d2b33
