# HEARTBEAT.md

# Keep this file empty (or with only comments) to skip heartbeat API calls.

# Add tasks below when you want the agent to check something periodically.

## 每日9:00 资讯同步任务
- 读取微信公众号RSS源 (45个)
- 筛选重要资讯 (30条)
- 同步到Notion
- 发送Discord消息

# 定时任务 (crontab)
0 9 * * * python3 ~/.openclaw/workspace-dev/scripts/daily_news_sync.py
