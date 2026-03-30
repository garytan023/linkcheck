#!/usr/bin/env python3
"""
每日微信公众号资讯同步脚本
- 读取RSS源
- 筛选重要资讯
- 同步到Notion
- 发送Discord消息
"""

import requests
import json
import os
from datetime import datetime, timedelta

NOTION_KEY = os.environ.get("NOTION_KEY", "")
NOTION_PAGE_ID = "31cdb0fc-025f-8141-b46a-fcd7976c3537"
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK", "")
DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")

# 验证必要环境变量
_missing = [k for k, v in {"NOTION_KEY": NOTION_KEY, "DISCORD_WEBHOOK": DISCORD_WEBHOOK, "DISCORD_BOT_TOKEN": DISCORD_BOT_TOKEN}.items() if not v]
if _missing:
    raise EnvironmentError(f"缺少环境变量: {', '.join(_missing)}，请在运行前设置")

RSS_SERVER = "http://8.138.40.155:9001/feed"
OPML_FILE = "/Users/garytan/.openclaw/workspace-dev/data/wechat_rss_subscriptions.opml"

# RSS源列表（从OPML提取的关键源）
RSS_SOURCES = {
    "AI科技": [
        "MP_WXS_3264997043",  # 腾讯AI实验室
        "MP_WXS_2395492220",  # AI投资
        "MP_WXS_2396014160",  # 新AI技术
    ],
    "电商零售": [
        "MP_WXS_3294797932",  # 电商头条
        "MP_WXS_3074474131",  # 京东黑板报
    ],
    "营销增长": [
        "MP_WXS_1432156401",  # 36氪
        "MP_WXS_2399237400",  # 增长官
        "MP_WXS_2392621067",  # 营销洞察
    ]
}

def fetch_rss(source_id):
    """抓取单个RSS源"""
    try:
        url = f"{RSS_SERVER}/{source_id}.atom"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            return resp.text
    except:
        pass
    return None

def parse_entries(xml_text, days=2):
    """解析RSS条目，筛选近N天的内容"""
    # 简化解析 - 实际可用feedparser
    entries = []
    import re
    # 提取title和link
    titles = re.findall(r'<title>([^<]+)</title>', xml_text)
    links = re.findall(r'<link[^>]*href="([^"]+)"', xml_text)
    # 去重
    seen = set()
    for i, title in enumerate(titles[2:]):  # 跳过前两个（feed title和subtitle）
        if title not in seen and len(entries) < 50:
            seen.add(title)
            link = links[i+1] if i+1 < len(links) else ""
            entries.append({"title": title, "link": link})
    return entries

def format_notion_blocks(news_items):
    """格式化Notion blocks"""
    blocks = []
    current_category = None
    
    for i, item in enumerate(news_items):
        category = item.get("category", "")
        
        # 分类标题
        if category != current_category:
            if blocks:
                blocks.append({"object": "block", "type": "divider", "divider": {}})
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": category}}]}
            })
            current_category = category
        
        # 条目
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{
                    "type": "text",
                    "text": {
                        "content": f"{i+1}. {item['title']}",
                        "link": {"url": item['link']} if item.get('link') else None
                    }
                }]
            }
        })
    
    return blocks

def sync_to_notion(blocks):
    """同步到Notion"""
    # 先删除旧内容
    url = f"https://api.notion.com/v1/blocks/{NOTION_PAGE_ID}/children?page_size=100"
    headers = {
        "Authorization": f"Bearer {NOTION_KEY}",
        "Notion-Version": "2025-09-03",
        "Content-Type": "application/json"
    }
    
    # 获取旧block (page_size parameter removed)
    resp = requests.get(f"https://api.notion.com/v1/blocks/{NOTION_PAGE_ID}/children", headers=headers)
    if resp.status_code == 200:
        old_blocks = resp.json().get("results", [])
        # 删除旧block (最多99个一批)
        for bb in old_blocks[:99]:
            del_url = f"https://api.notion.com/v1/blocks/{bb['id']}"
            requests.delete(del_url, headers=headers)
    
    # 添加新block (分批，每批100)
    for i in range(0, len(blocks), 100):
        batch = blocks[i:i+100]
        resp = requests.patch(url, headers=headers, json={"children": batch})
        if resp.status_code != 200:
            print(f"Notion sync error: {resp.text}")

def send_discord(news_items):
    """发送Discord消息"""
    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    
    today = datetime.now().strftime("%Y年%m月%d日")
    msg = f"📰 **微信公众号精选摘要 | {today}**\n\n"
    
    current_cat = None
    for i, item in enumerate(news_items):
        cat = item.get("category", "")
        if cat != current_cat:
            msg += f"\n**{cat}**\n"
            current_cat = cat
        msg += f"{i+1}. {item['title']}\n{item.get('link', '')}\n"
    
    # 截断过长消息
    if len(msg) > 1800:
        msg = msg[:1800] + "\n...(查看完整版)"
    
    requests.post(DISCORD_WEBHOOK, headers=headers, json={"content": msg})

def main():
    """主函数"""
    print("开始抓取RSS...")
    
    all_news = []
    
    # 抓取各分类RSS
    for category, sources in RSS_SOURCES.items():
        for source in sources:
            content = fetch_rss(source)
            if content:
                entries = parse_entries(content)
                for e in entries:
                    e["category"] = category
                    all_news.append(e)
    
    # 去重并取前30条
    seen = set()
    unique_news = []
    for n in all_news:
        if n["title"] not in seen:
            seen.add(n["title"])
            unique_news.append(n)
            if len(unique_news) >= 30:
                break
    
    print(f"获取到 {len(unique_news)} 条资讯")
    
    # 同步到Notion
    blocks = format_notion_blocks(unique_news)
    sync_to_notion(blocks)
    print("Notion同步完成")
    
    # 发送Discord
    send_discord(unique_news)
    print("Discord发送完成")

if __name__ == "__main__":
    main()
