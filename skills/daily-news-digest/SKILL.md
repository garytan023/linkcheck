# daily-news-digest

每日电商/营销/媒介行业资讯精选。抓取微信公众号 RSS 源 → AI 评分筛选 → 生成飞书文档 → 发送飞书消息通知 Gary。

## 快速执行

```bash
python3 ~/.openclaw/workspace-dev/skills/daily-news-digest/scripts/rss_digest.py
```

执行后输出：
- 本地 Markdown：`~/.openclaw/workspace-dev/output/rss_daily_YYYY-MM-DD.md`
- 飞书文档链接（打印到 stdout）

## 工作流程

1. **抓取** - 并行抓取 45 个 RSS 源（微信公众号 via RSSHub 代理 `http://s.ztso.xyz:11211/feed/`）
2. **去重** - 按标题指纹排重 + 噪音词过滤
3. **日期过滤** - 只保留昨天内容
4. **排他分类** - 每篇文章只归一个最相关分类（京东/字节/阿里妈妈/小红书/腾讯/百度/营销+AI/电商零售/营销增长）
5. **AI 评分** - 按营销洞察/案例+媒介投放+电商运营+AI营销打分
6. **精选** - 每分类最多 8 条，按分数降序
7. **生成文档** - 写入飞书云文档
8. **通知** - 发飞书 DM 给 Gary，包含文档链接

## 关键文件

- `scripts/rss_digest.py` - 主脚本（v4，排他性分类 + 新分类体系）
- `scripts/rss_digest.py` 中 `OPML_FILE` 指向 `~/.openclaw/workspace-dev/data/wechat_rss_subscriptions.opml`
- `OUTPUT_FILE` 输出到 `~/.openclaw/workspace-dev/output/rss_daily_YYYY-MM-DD.md`

## RSS 代理

使用 `http://s.ztso.xyz:11211/feed/` 作为 RSSHub 代理。

## 分类说明

### 排他性分类逻辑（按优先级）

1. 来源账号直接映射（SOURCE_PLATFORM_MAP）→ 对应平台分类
2. 关键词匹配兜底：
   - 小红书关键词 → 小红书
   - 京东关键词 → 京东
   - 阿里妈妈关键词 → 阿里妈妈
   - 字节/抖音/巨量关键词 → 字节
   - 腾讯/微信/腾讯广告关键词 → 腾讯
   - 百度关键词 → 百度
   - AI相关关键词 → 营销+AI
   - 电商/零售/直播关键词 → 电商零售
   - 其他 → 营销增长

### 分类体系（v4）

| 分类 | Emoji | 说明 |
|------|-------|------|
| 京东 | 🟣 | 京东平台相关 |
| 字节 | 🔵 | 抖音/字节/巨量引擎相关 |
| 阿里妈妈 | 🟠 | 阿里妈妈/淘宝/天猫相关 |
| 小红书 | 🔴 | 小红书平台相关 |
| 腾讯 | 🟢 | 腾讯/微信/腾讯广告相关 |
| 百度 | ⚪ | 百度营销相关 |
| 营销+AI | 🤖 | AI+营销/技术相关 |
| 电商零售 | 🛒 | 电商/零售/直播相关 |
| 营销增长 | 📈 | 营销增长/案例/策略相关 |

### 分类优先级

`CAT_ORDER = ['京东', '字节', '阿里妈妈', '小红书', '腾讯', '百度', '营销+AI', '电商零售', '营销增长']`

## Cron 调度（6:30 AM 每日）

Job ID: `47ab2b45-8094-48a4-97ab-3d782bcfb740`
```
30 6 * * * python3 ~/.openclaw/workspace-dev/skills/daily-news-digest/scripts/rss_digest.py
```

## 发送通知

cron job 的 `agentTurn` prompt 指示 agent：
1. 运行脚本获取文档 URL
2. 用 `feishu_create_doc` 创建飞书文档
3. 用 `message(action=send, channel=feishu, to=user:ou_d635f4f3d20ac474cf8575038b5d2b33, message=...)` 发送摘要卡片

## 已知限制

- 微信公众号 RSS 不暴露阅读量/在看/评论等互动指标
- 互动数据如有需要，需通过新榜/蝉妈妈/飞瓜数据 API（付费）
