# 每日资讯同步 SOP

## 概述
每天早上9点自动抓取微信公众号精选资讯，同步到飞书群和Notion。

## 数据源
- RSS服务器: `http://8.138.40.155:9001/feed`
- 订阅源: `~/.openclaw/workspace-dev/data/wechat_rss_subscriptions.opml` (45个公众号)
- 关键词分类脚本: `~/.openclaw/workspace-dev/scripts/daily_news_sync_v2.py`

## 执行流程

### Step 1: RSS抓取
```bash
python3 ~/.openclaw/workspace-dev/scripts/daily_news_sync_v2.py
```

### Step 2: 日期过滤
- 只抓取**昨日**内容
- 格式: YYYY-MM-DD

### Step 3: 关键词分类
| 分类 | 关键词 |
|------|--------|
| 营销+AI | ai/gpt/openclaw/kimi/大模型/agent/智能/机器人/nano banana/gemini/claude/文心/通义/豆包 |
| 京东 | 含"京东" |
| 抖音 | 抖音/字节/tiktok |
| 阿里妈妈 | 阿里妈妈/万堂书院/直通车 |
| 小红书 | 含"小红书" |
| 电商零售 | 电商/零售/店铺/销量/直播带货/gmv/商家/拼多多/天猫/淘宝 |
| 营销增长 | 营销/增长/投放/广告/案例/品牌/趋势/消费者/种草/带货 |

### Step 4: 筛选逻辑 (重要!)
- **最多筛选40条**以内
- 优先级: 营销+AI > 营销增长 > 电商零售 > 抖音 > 京东 > 小红书 > 阿里妈妈
- 每个分类按实际数量输出，不硬凑

### Step 5: 输出格式
```
📰 每日精选资讯 | YYYY年MM月DD日

🤖 营销+AI (X条)
• 标题
  链接

🛒 电商零售 (X条)
...
```

### Step 6: 同步渠道

#### 飞书群
- 发送消息到群: `oc_b981dd57ea7a10253ec4a58ed77a887e`
- 内容: 纯文本格式

#### Notion
- 页面: "每日资讯" (id: 31cdb0fc-025f-8141-b46a-fcd7976c3537)
- 格式: H1标题 → H2分类 → Paragraph每条(标题+链接)
- API Key: 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

#### Discord (可选)
- 频道ID: 1478997781187268608

## 定时任务
```bash
# 每天早上9点执行
0 9 * * * python3 ~/.openclaw/workspace-dev/scripts/daily_news_sync_v2.py >> ~/.openclaw/logs/daily_news.log 2>&1
```

## 常见问题

### RSS服务器连不上
- 检查: `curl http://8.138.40.155:9001/feed`
- 重试机制: 脚本内置自动重试

### 飞书文档写入失败 (404)
- 原因: APP token没有docx:document:content权限
- 解决: 在飞书开放平台添加权限

### Notion写入失败 (SSL错误)
- 原因: 网络不稳定
- 解决: 分批写入，每条间隔0.5秒

## 相关文件
- 脚本: `~/.openclaw/workspace-dev/scripts/daily_news_sync_v2.py`
- 订阅源: `~/.openclaw/workspace-dev/data/wechat_rss_subscriptions.opml`
- 日志: `~/.openclaw/logs/daily_news.log`
- 飞书文档: `https://open.feishu.cn/document/xxxx`
- Notion页面: `https://notion.so/31cdb0fc025f8141b46afcd7976c3537`

---
*最后更新: 2026-03-11*
