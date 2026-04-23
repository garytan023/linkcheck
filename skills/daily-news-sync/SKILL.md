# 每日资讯同步 skill

## 目标
每日9点自动抓取微信公众号RSS资讯 → AI评分精选40条 → 脚本直发飞书IM + 创建飞书文档存档

## 全自动流程（彻底固化）

cron job "每日资讯精选 09:00" 每天9:00运行：
1. Agent 执行 `python3 ~/.openclaw/workspace-dev/scripts/daily_news_sync_v4.py`
2. 脚本自动完成：抓取 → AI分类 → 精选40条 → 发飞书IM + 创飞书文档
3. Agent 检查脚本输出中的 `[Feishu IM]` 和 `[Feishu Doc]` 结果

**无需 Agent 介入发送环节**（脚本自己调用飞书API）

---

## 脚本输出格式

### 飞书IM消息（全部40条，一条消息）
```
📋 每日资讯精选 2026-04-22 | 完整40条

🟣 京东（6条）
京东广告2026三大升级：引领营销迈入"品牌全方位建设"新时代
https://mp.weixin.qq.com/s/K3jaKT0D6pRU2tfsQHEVyQ
京东大药房发布新十年蓝图：AI助力打造100个十亿级品牌
https://mp.weixin.qq.com/s/e6mdAUoyvtjrjnInhZeUvA
...

🔵 字节（3条）
...

🟠 阿里妈妈（1条）
...

🔴 小红书（3条）
...

🟢 腾讯（2条）
...

⚪ 百度（3条）
...

🤖 营销+AI（8条）
...

🛒 电商零售（10条）
...

📈 营销增长（22条）
...

📄 完整版（40条全文）：https://www.feishu.cn/docx/xxx
```

**格式规则**：
- 每条新闻：标题一行 + 链接下一行（Gary要求）
- 不省略任何一条，全部40条一口气发出
- 消息末尾附飞书文档链接

### 分类emoji
- 🟣 京东  🔵 字节  🟠 阿里妈妈  🔴 小红书  🟢 腾讯  ⚪ 百度
- 🤖 营销+AI  🛒 电商零售  📈 营销增长

---

## 脚本关键文件
- 主脚本：`~/.openclaw/workspace-dev/scripts/daily_news_sync_v4.py`
- RSS源列表：`~/.openclaw/workspace-dev/data/wechat_rss_subscriptions.opml`
- RSS代理：`http://s.ztso.xyz:11211/feed/`
- 输出目录：`~/.openclaw/workspace-dev/output/rss_daily_YYYY-MM-DD.md`

## 分类体系（9类）
`CAT_ORDER = ['京东', '字节', '阿里妈妈', '小红书', '腾讯', '百度', '营销+AI', '电商零售', '营销增长']`

### Python粗分类（平台账号映射）
京东/字节/阿里妈妈/小红书/腾讯/百度 账号直接映射到对应分类

### AI智能重分类
其余文章按内容分入：
- **营销+AI**：AI工具在营销/广告/投放中的实际应用（AI辅助投放工具、AI生成广告素材、Agent落地案例）
- **电商零售**：电商平台运营、选品、供应链、直播带货、货架电商、跨境出口
- **营销增长**：营销案例/洞察/策略/趋势/数据/报告/白皮书

---

## 手动测试
```bash
python3 ~/.openclaw/workspace-dev/scripts/daily_news_sync_v4.py
```
观察输出中的 `[Feishu IM] 发送成功` 和 `[Feishu Doc] 创建成功`

## 故障排查
1. **RSS抓取全挂** → 检查代理 `http://s.ztso.xyz:11211/feed/` 是否恢复
2. **Feishu IM发送失败** → 检查 `FEISHU_APP_ID`, `FEISHU_APP_SECRET`, `FEISHU_USER_OPENID` 环境变量
3. **Feishu Doc创建失败** → 同上，检查飞书API权限
4. **超时** → cron已改为脚本直发，不再走Agent超时路径
