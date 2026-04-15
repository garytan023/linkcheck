# 每日资讯同步 skill

## 目标
每日9点自动抓取微信公众号RSS资讯，同步到飞书文档

---

## 输入
- RSS服务器: `http://8.138.40.155:9001/feed`
- 公众号列表（25个核心源）:
  ```
  营销+AI: SocialBeta, TopDigital
  电商零售: 天下网商, 老高电商, 手淘集团
  营销增长: 虎嗅APP, 腾讯广告, 寻空, Marteker, 刀法, 胖鲸
  小红书: REDtech, 商业动态, 种草学
  京东: 黑板报, 研究院, 京麦
  抖音: 抖音电商营销观察
  阿里妈妈: 数字营销, 万堂书院
  ```

---

## 处理流程

### Step 1: 连接RSS服务器抓取
```python
# 正确方式：用XML解析器（不是正则！）
from xml.etree import ElementTree
root = ElementTree.fromstring(resp.text)
ns = {'atom': 'http://www.w3.org/2005/Atom'}
entries = root.findall('atom:entry', ns)
for entry in entries:
    title = entry.find('atom:title', ns)
    link = entry.find('atom:link', ns)
    updated = entry.find('atom:updated', ns)
```

### Step 2: 日期过滤
- **只取昨日内容**（今日9点同步昨日资讯）
- 日期格式: `2026-03-09`

### Step 3: 关键词分类（不是按公众号分类！）
```python
def classify(title):
    t = title
    if any(k in t.lower() for k in ['ai', 'gpt', 'openclaw', 'kimi', '大模型', 'agent', '智能', '机器人']):
        return '营销+AI'
    if '京东' in t: return '京东'
    if any(k in t for k in ['抖音', '字节']): return '抖音'
    if any(k in t for k in ['阿里妈妈', '万堂书院']): return '阿里妈妈'
    if '小红书' in t: return '小红书'
    if any(k in t.lower() for k in ['电商', '零售', '店铺', '销量', '直播', '爆卖', 'gmv', '商家', '天猫', '淘宝']):
        return '电商零售'
    if any(k in t.lower() for k in ['营销', '增长', '投放', '广告', '案例', '品牌', '趋势']):
        return '营销增长'
    return '其他'
```

### Step 4: 输出数量
- 按昨日实际数量输出，不硬凑
- 分类: 营销+AI、电商零售、营销增长、小红书、京东、抖音、阿里妈妈

### Step 5: 飞书文档
- 标题格式: `每日精选资讯 | YYYY年MM月DD日`
- 每条: 标题 + 原文链接（分开两行）
- 分类带emoji: 🤖🛒📈📱🎵💰

### Step 6: 权限
- 立即开放 full_access 给 Gary (openid: ou_d635f4f3d20ac474cf8575038b5d2b33)

---

## 输出格式
```
📰 微信公众号精选摘要 | 2026年3月10日
（昨日3月9日内容）

🤖 营销+AI (9条)
标题1
链接1
标题2
链接2
...

🛒 电商零售 (6条)
...
```

---

## 常见问题
1. **RSS服务器挂了** → 等15分钟重试
2. **标题链接对不上** → 用XML解析器，不是正则
3. **内容不够** → 放宽到3天，但要在文档中注明
4. **Discord发不出去** → Token失效，需要更新

---

## ⚠️ 已知问题

### 飞书文档创建后内容为空
**原因**: APP缺少 `docx.content:writer` 权限，写入API返回404

**解决方案**:
1. 创建文档后，用 `feishu_update_doc` 工具写入内容:
   ```json
   {
     "doc_id": "文档ID",
     "markdown": "内容...",
     "mode": "overwrite"
   }
   ```
2. 或者在飞书开放平台给APP添加 `docx.content:writer` 权限

### 权限设置成功但文档无内容
- 脚本已能创建文档 + 设置权限
- 需要用 feishu_update_doc 工具补充写入内容

---

## ✅ 最终方案（2026-03-10确认）

### 流程
1. **脚本** (`daily_news_sync_v2.py`): 创建飞书文档 + 设置权限 + 输出内容
2. **feishu_doc工具**: 写入内容（用用户token，绕过APP权限限制）

### 关键点
- 脚本创建文档后，打印 `doc_id` 和 `===CONTENT_START===...===CONTENT_END===`
- 用 `feishu_update_doc` 工具写入:
  ```json
  {
    "doc_id": "文档ID",
    "markdown": "内容...",
    "mode": "overwrite"
  }
  ```

### 自动运行
- 定时任务会在9点自动运行
- 脚本输出后，自动调用 feishu_doc 工具写入
