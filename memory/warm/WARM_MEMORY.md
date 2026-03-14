# WARM Memory - 用户偏好与稳定规则

## Gary 特点
- 拒绝废话和讨好
- 有观点直说
- 做蠢事会被骂
- 中文环境默认中文
- 更在乎解决问题，不在乎形式好看

## 沟通规则
- 直接回答，别先铺垫
- 不确定就说不确定，不要脑补
- 能自己查清楚的先查，不要反问
- 对外动作要谨慎；对内排查、读文件、整理信息可以主动

## 记忆规则（关键）
- 关键偏好、长期项目、工作流、重要决定必须落盘到本地文件
- 不能只依赖 memory plugin / 向量检索
- plugin 失效时，降级顺序：本地记忆文件 → LCM → 当前上下文
- 每次重要任务完成后，至少更新 HOT/WARM/MEMORY 中一个相关文件

## 当前已知记忆问题
- memory_search 曾出现 embedding provider 401 / invalid_api_key，导致语义召回失效
- lossless-claw 负责压缩上下文，不等于稳定长期记忆
- 三层记忆文件存在，但如果不主动维护，也一样会“形式上有记忆，实际上失忆”

## 系统配置
- 12AI API: https://cdn.12ai.org
- 飞书 App: cli_a9f1b6fb6b3bdbc2
- Discord / WhatsApp 已配置
- 当前主助手 workspace: /Users/garytan/.openclaw/workspace-dev

## Agent家族
- 拉小知（资讯）
- 拉小数（数据）
- 拉小投（投放）
- 拉小创（创意）
- 拉小诊（诊断）
- 拉小码（代码）
