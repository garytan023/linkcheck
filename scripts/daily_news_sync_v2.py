#!/usr/bin/env python3
"""
每日微信公众号资讯同步 - 优化版
45个公众号 + 关键词分类 + 飞书文档
支持并行抓取
"""
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import json
import os
import threading

# 验证必要环境变量
_missing = [k for k, v in {
    "DISCORD_BOT_TOKEN": DISCORD_BOT_TOKEN,
    "FEISHU_APP_ID": FEISHU_APP_ID,
    "FEISHU_APP_SECRET": FEISHU_APP_SECRET,
}.items() if not v]
if _missing:
    raise EnvironmentError(f"缺少环境变量: {', '.join(_missing)}，请在运行前设置")
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

RSS_SERVER = 'http://8.138.40.155:9001/feed'
OPML_FILE = os.path.expanduser('~/.openclaw/workspace-dev/data/wechat_rss_subscriptions.opml')
CHECKPOINT_FILE = os.path.expanduser('~/.openclaw/workspace-dev/data/daily_news_checkpoint.json')

# Discord channel ID
DISCORD_CHANNEL_ID = '1478997781187268608'
# Discord bot token
DISCORD_BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN', '')

# 飞书配置
FEISHU_APP_ID = os.environ.get('FEISHU_APP_ID', '')
FEISHU_APP_SECRET = os.environ.get('FEISHU_APP_SECRET', '')
FEISHU_USER_OPENID = 'ou_d635f4f3d20ac474cf8575038b5d2b33'

CAT_EMOJI = {
    '营销+AI': '🤖', '电商零售': '🛒', '营销增长': '📈',
    '小红书': '📱', '京东': '🛍️', '抖音': '🎵', '阿里妈妈': '💰'
}

_session = None
_seen_lock = threading.Lock()


def get_session():
    """复用 HTTP 连接，并对临时失败自动重试"""
    global _session
    if _session is None:
        s = requests.Session()
        retry = Retry(
            total=2,
            connect=2,
            read=2,
            backoff_factor=0.8,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry, pool_connections=20, pool_maxsize=20)
        s.mount('http://', adapter)
        s.mount('https://', adapter)
        s.headers.update({'User-Agent': 'daily-news-sync/2.1'})
        _session = s
    return _session


def load_sources_from_opml():
    """从OPML文件加载所有公众号来源"""
    try:
        tree = ET.parse(OPML_FILE)
        root = tree.getroot()
        sources = []
        for outline in root.findall('.//outline'):
            title = outline.get('title', '')
            xml_url = outline.get('xmlUrl', '')
            if xml_url and 'MP_WXS_' in xml_url:
                # 从URL提取ID: http://8.138.40.155:9001/feed/MP_WXS_xxx.atom
                sid = xml_url.split('/')[-1].replace('.atom', '')
                sources.append({'id': sid, 'name': title})
        return sources
    except Exception as e:
        print(f"Error loading OPML: {e}")
        return []


def parse_feed(sid, name):
    """用XML解析器抓取单个源，输出可诊断日志"""
    url = f'{RSS_SERVER}/{sid}.atom'
    try:
        resp = get_session().get(url, timeout=(4, 10))
        if resp.status_code != 200:
            print(f"[WARN] {name} status={resp.status_code} url={url}")
            return []

        root = ET.fromstring(resp.content)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}

        items = []
        for entry in root.findall('atom:entry', ns):
            title = entry.find('atom:title', ns)
            link = entry.find('atom:link', ns)
            updated = entry.find('atom:updated', ns)

            if title is not None and link is not None:
                title_text = title.text.strip() if title.text else ''
                link_href = link.get('href', '')

                pub_date = None
                if updated is not None and updated.text:
                    try:
                        from email.utils import parsedate_to_datetime
                        pub_date = parsedate_to_datetime(updated.text)
                    except Exception:
                        pass

                if title_text and len(title_text) > 5:
                    items.append({
                        'title': title_text,
                        'link': link_href,
                        'date': pub_date,
                        'source': name
                    })
        return items
    except Exception as e:
        print(f"[ERR] {name} url={url} err={type(e).__name__}: {e}")
        return []


def save_checkpoint(yesterday, completed, total, stats, all_items):
    data = {
        'date': yesterday,
        'completed': completed,
        'total_sources': total,
        'stats': stats,
        'items': all_items,
        'saved_at': datetime.now().isoformat()
    }
    with open(CHECKPOINT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)



def fetch_all_feeds_parallel(sources, yesterday_date, yesterday, max_workers=5):
    """并行抓取所有RSS源，边抓边写 checkpoint，超时也保留部分结果"""
    all_items = []
    seen = set()
    stats = {'ok': 0, 'empty': 0, 'failed': 0}

    def fetch_one(src):
        sid = src['id']
        name = src['name']
        items = parse_feed(sid, name)
        result = []
        matched = 0
        for item in items:
            if item['date'] and item['date'].date() == yesterday_date:
                matched += 1
                title = item['title']
                if title:
                    with _seen_lock:
                        if title in seen:
                            continue
                        seen.add(title)
                    cat = classify(title)
                    result.append({
                        'title': title,
                        'link': item['link'],
                        'cat': cat,
                        'source': item['source']
                    })
        return name, matched, result, len(items)

    print(f"开始并行抓取 {len(sources)} 个来源 (并发数: {max_workers})...")
    save_checkpoint(yesterday, 0, len(sources), stats, all_items)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_one, src): src for src in sources}
        completed = 0
        for future in as_completed(futures):
            completed += 1
            src = futures[future]
            name = src['name']
            try:
                name, matched, items, total_items = future.result()
                all_items.extend(items)
                if total_items == 0:
                    stats['failed'] += 1
                elif matched == 0:
                    stats['empty'] += 1
                else:
                    stats['ok'] += 1
                print(f"  [{completed:02d}/{len(sources)}] {name}: feed={total_items} yesterday={matched} selected={len(items)}")
            except Exception as e:
                stats['failed'] += 1
                print(f"  [{completed:02d}/{len(sources)}] {name}: FAILED {type(e).__name__}: {e}")
            save_checkpoint(yesterday, completed, len(sources), stats, all_items)

    print(f"抓取完成，共 {len(all_items)} 条昨日资讯 | ok={stats['ok']} empty={stats['empty']} failed={stats['failed']}")
    return all_items


def classify(title):
    """关键词分类"""
    t = title
    if any(k in t.lower() for k in ['ai', 'gpt', 'openclaw', 'kimi', '大模型', 'agent', '智能', '机器人', 'nano banana', 'gemini', 'claude', '文心', '通义', '豆包', 'minimax']):
        return '营销+AI'
    if '京东' in t:
        return '京东'
    if any(k in t for k in ['抖音', '抖音商城', '抖音电商', '字节', 'tiktok']):
        return '抖音'
    if any(k in t for k in ['阿里妈妈', '万堂书院', '直通车', '引力']):
        return '阿里妈妈'
    if '小红书' in t:
        return '小红书'
    if any(k in t.lower() for k in ['电商', '零售', '店铺', '销量', '直播', '爆卖', 'gmv', '订单', '商家', '外卖', '拼多多', '天猫', '淘宝']):
        return '电商零售'
    if any(k in t.lower() for k in ['营销', '增长', '投放', '广告', '案例', '传播', '用户', '流量', '转化', '私域', '种草', '品牌', '消费者', '趋势', '财报', 'ceo', '行业']):
        return '营销增长'
    return '其他'


def get_feishu_token():
    """获取飞书Token"""
    url = 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal'
    resp = requests.post(url, json={'app_id': FEISHU_APP_ID, 'app_secret': FEISHU_APP_SECRET})
    if resp.status_code == 200:
        data = resp.json()
        if data.get('code') == 0:
            return data.get('tenant_access_token')
    return None


def create_feishu_doc(title, content):
    """创建飞书文档 - 现在只输出内容供 Agent 使用 feishu_create_doc 写入"""
    # 输出内容标记，供 Agent 读取
    print("\n" + "="*60)
    print("FEISHU_CONTENT_START")
    print(content)
    print("FEISHU_CONTENT_END")
    print("="*60)
    
    # 输出 doc title
    print(f"\nFEISHU_TITLE: {title}")
    
    return title, title, content  # 返回 title 作为标识


def send_discord(content):
    """发送Discord消息"""
    if not DISCORD_BOT_TOKEN or not DISCORD_CHANNEL_ID:
        print("⚠️ Discord配置未完成，跳过Discord发送")
        return False
    
    headers = {
        'Authorization': f'Bot {DISCORD_BOT_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    # Discord每个消息最多2000字符，需要分片
    max_len = 1900
    chunks = []
    for i in range(0, len(content), max_len):
        chunks.append(content[i:i+max_len])
    
    for chunk in chunks:
        url = f'https://discord.com/api/v10/channels/{DISCORD_CHANNEL_ID}/messages'
        resp = requests.post(url, headers=headers, json={'content': chunk})
        if resp.status_code not in (200, 201):
            print(f"Discord发送失败: {resp.status_code} - {resp.text}")
            return False
    return True


def main():
    # 昨日日期
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    yesterday_date = datetime.strptime(yesterday, '%Y-%m-%d').date()
    
    print(f"=== 每日资讯同步 | {yesterday} ===")
    
    # 加载全部45个来源
    sources = load_sources_from_opml()
    print(f"加载了 {len(sources)} 个公众号来源")
    
    # 并行抓取全部
    all_items = fetch_all_feeds_parallel(sources, yesterday_date, yesterday, max_workers=5)
    
    # 分类
    cats = {cat: [] for cat in CAT_EMOJI.keys()}
    other_items = []
    for item in all_items:
        if item['cat'] in cats:
            cats[item['cat']].append(item)
        else:
            other_items.append(item)
    
    # 输出统计
    for cat in CAT_EMOJI.keys():
        print(f"  {cat}: {len(cats[cat])}条")
    print(f"  其他: {len(other_items)}条")
    
    # 精选40条：营销+AI 5条 + 电商零售 8条 + 营销增长 10条 + 小红书/京东/抖音/阿里妈妈 共7条
    TARGET_COUNTS = {
        '营销+AI': 8,
        '电商零售': 10,
        '营销增长': 12,
        '小红书': 4,
        '京东': 3,
        '抖音': 3,
        '阿里妈妈': 0
    }
    
    # 精选内容
    selected_items = []
    for cat, target in TARGET_COUNTS.items():
        items = cats.get(cat, [])
        # 取前target条
        selected_items.extend(items[:target])
    
    # 如果还不够30条，从其他分类补充
    if len(selected_items) < 40:
        remaining = 40 - len(selected_items)
        # 从"其他"分类中补充
        for item in other_items[:remaining]:
            # 尝试归类到主要分类
            item['cat'] = classify(item['title'])
            if item['cat'] in cats:
                selected_items.insert(0, item)
    
    # 重新按分类组织
    selected_cats = {cat: [] for cat in CAT_EMOJI.keys()}
    for item in selected_items:
        if item['cat'] in selected_cats:
            selected_cats[item['cat']].append(item)
    
    # 生成内容
    today_str = datetime.now().strftime('%Y年%m月%d日')
    content = f"📰 微信公众号精选摘要 | {today_str}\n（昨日{yesterday}内容，共{len(selected_items)}条）\n\n"
    
    for cat in CAT_EMOJI.keys():
        items = selected_cats[cat]
        if not items:
            continue
        emoji = CAT_EMOJI[cat]
        content += f"\n{emoji} {cat} ({len(items)}条)\n"
        for item in items:
            content += f"{item['title']}\n{item['link']}\n"
    
    # 发送到飞书
    doc_title = f"每日精选资讯 | {today_str}"
    
    # 创建文档（输出内容供 Agent 使用 feishu_create_doc 写入）
    doc_title, doc_url, content = create_feishu_doc(doc_title, content)
    
    print(f"\n✅ 脚本执行完成")
    print(f"请使用 feishu_create_doc 工具创建飞书文档，标题: {doc_title}")
    print(f"内容见上方 FEISHU_CONTENT 标记")




if __name__ == '__main__':
    main()

