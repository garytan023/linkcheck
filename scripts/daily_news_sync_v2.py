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
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

RSS_SERVER = 'http://s.ztso.xyz:11211/feed'
OPML_FILE = os.path.expanduser('~/.openclaw/workspace-dev/data/wechat_rss_subscriptions.opml')
CHECKPOINT_FILE = os.path.expanduser('~/.openclaw/workspace-dev/data/daily_news_checkpoint.json')
DEDUP_HISTORY_FILE = os.path.expanduser('~/.openclaw/workspace-dev/data/daily_news_dedup_history.json')
DEDUP_DAYS = 7

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


def is_noise(title):
    """识别广告软文 / 招聘内容，排除噪音
    原则：只过滤明显的广告/招聘/诱导，内容型文章保留
    """
    t = (title or '')
    tl = t.lower()

    # 招聘类：标题本身就是招聘JD，不是内容报道
    if any(k in t for k in ['【诚聘】', '【招聘】', '【急招】', '诚聘', '加入我们', '猎头', 'HR诚聘', '高薪诚聘',
                       '薪资面议', '跳槽', 'offer直达', 'offer', '面试', '入职', '简历投递']):
        return True

    # 软文/促销：标题里有明确的买卖诱导，无实质内容价值
    if any(k in t for k in ['免费领', '限时抢', '立即购买', '优惠码', '满减', '0元购', '1元购',
                             '惊喜价', '优惠价', '全网首发', '限时优惠', '0门槛']):
        return True

    # 诱导分享/收藏类
    if any(k in t for k in ['转给朋友', '扩散', '建议收藏', '朋友圈', '求求了', '救命']):
        return True

    return False


def normalize_text(text):
    """归一化标题，用于软去重"""
    if not text:
        return ''
    t = text.strip().lower()
    for ch in ['【', '】', '[', ']', '（', '）', '(', ')', '｜', '|', '：', ':', '，', ',', '。', '.', '！', '!', '？', '?', '“', '”', '"', "'", '、', '/', '-', '_']:
        t = t.replace(ch, ' ')
    return ' '.join(t.split())


def title_fingerprint(title):
    """标题指纹：去掉噪音后取核心特征"""
    normalized = normalize_text(title)
    tokens = [tok for tok in normalized.split() if len(tok) > 1]
    return ' '.join(tokens[:12])


def load_dedup_history():
    """加载近N天已发送历史"""
    if not os.path.exists(DEDUP_HISTORY_FILE):
        return []
    try:
        with open(DEDUP_HISTORY_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return data.get('items', []) if isinstance(data, dict) else []
    except Exception as e:
        print(f"[WARN] load dedup history failed: {e}")
        return []


def save_dedup_history(history_items):
    """保存近N天已发送历史，仅保留窗口期数据"""
    cutoff = (datetime.now() - timedelta(days=DEDUP_DAYS)).date()
    kept = []
    for item in history_items:
        try:
            item_date = datetime.strptime(item.get('date', ''), '%Y-%m-%d').date()
            if item_date >= cutoff:
                kept.append(item)
        except Exception:
            continue

    payload = {
        'days': DEDUP_DAYS,
        'updated_at': datetime.now().isoformat(),
        'items': kept
    }
    with open(DEDUP_HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def deduplicate_items(items, history_items, current_date):
    """近N天去重：同链接 / 同标题 / 同标题指纹 都过滤"""
    seen_links = set()
    seen_titles = set()
    seen_fingerprints = set()

    for hist in history_items:
        link = (hist.get('link') or '').strip()
        title = (hist.get('title') or '').strip()
        fp = hist.get('fingerprint') or title_fingerprint(title)
        if link:
            seen_links.add(link)
        if title:
            seen_titles.add(title)
        if fp:
            seen_fingerprints.add(fp)

    unique_items = []
    dropped_items = []

    for item in items:
        link = (item.get('link') or '').strip()
        title = (item.get('title') or '').strip()
        fp = title_fingerprint(title)

        is_dup = False
        dup_reason = None
        if link and link in seen_links:
            is_dup = True
            dup_reason = 'same_link'
        elif title and title in seen_titles:
            is_dup = True
            dup_reason = 'same_title'
        elif fp and fp in seen_fingerprints:
            is_dup = True
            dup_reason = 'same_topic'

        if is_dup:
            item['dup_reason'] = dup_reason
            dropped_items.append(item)
            continue

        unique_items.append(item)
        if link:
            seen_links.add(link)
        if title:
            seen_titles.add(title)
        if fp:
            seen_fingerprints.add(fp)

    new_history = history_items + [
        {
            'date': current_date,
            'title': item.get('title', ''),
            'link': item.get('link', ''),
            'fingerprint': title_fingerprint(item.get('title', '')),
            'cat': item.get('cat', ''),
            'source': item.get('source', '')
        }
        for item in unique_items
    ]

    return unique_items, dropped_items, new_history


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
                    # 过滤广告软文和招聘
                    if is_noise(title):
                        continue
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
    """关键词分类 - 聚焦国内竞价媒体+国内电商，保持足够宽的匹配面"""
    t = title
    tl = t.lower()

    # 营销+AI
    if any(k in tl for k in ['ai', 'gpt', 'kimi', '大模型', 'agent', '智能', 'gemini', 'claude', '文心', '通义', '豆包', 'minimax', 'aigc', 'openclaw', 'openai', 'deepseek', 'qwen', '人工智能']):
        return '营销+AI'

    # 京东
    if any(k in t for k in ['京东', '京麦', '京挑客', '京东联盟', '京东商家', '京东站', '京东金融']):
        return '京东'

    # 抖音（国内抖音生态，不含tiktok海外）
    if any(k in t for k in ['抖音', '巨量千川', '巨量引擎', '字节', '抖店', '巨量', '抖音电商', '抖音直播', '抖音广告', '抖音小店', '抖音投放', '抖音种草', '抖音商城']):
        return '抖音'

    # 阿里妈妈（含拼多多竞价）
    if any(k in t for k in ['阿里妈妈', '万堂书院', '直通车', '引力魔方', '达摩盘', '品销宝', '钻展', '多多搜索', '多多场景', '淘系广告', '淘系投放', '超级推荐', '淘宝客', '淘特']):
        return '阿里妈妈'

    # 小红书（含站内投放工具）
    if any(k in t for k in ['小红书', '薯条', '蒲公英', '聚光', '小红书商家', '小红书电商', '小红书投放', '小红书种草', '小红书广告', '小红盟', 'REDtech']):
        return '小红书'

    # 电商零售（国内电商成交链路）
    if any(k in tl for k in ['电商', '直播带货', '直播电商', 'gmv', '天猫', '淘宝', '拼多多', '抖店', '快手电商', '快手小店', '电商运营', '电商投放', '电商转化', '电商案例', '电商复盘', '电商报告', '电商趋势', '电商数据', '电商分析', '商家', '店铺', '销量', '转化率', '客单价', '商品页', '种草', '带货', '零售', '外卖', '即时零售', '货架']):
        return '电商零售'

    # 营销增长（竞价+效果广告为核心，兼容泛商业营销内容）
    # 低门槛匹配：只要标题含营销/商业相关词，就进这个分类
    if any(k in tl for k in [
        '竞价', '付费媒体', '付费流量', '信息流', '效果广告',
        '投放', '投放策略', '投放案例', '投放复盘', '投放优化', '投放成本', '广告投放',
        '广告案例', '广告优化', '广告策略', '广告主', 'ocpx',
        '智能定向', '人群定向', '出价', '起量', '放量', '压成本', '降本',
        '营销', '增长', '获客', '转化', '私域', '品牌广告', '效果营销', '广告平台',
        '行业报告', '营销报告', '营销趋势', '趋势报告', '数据报告', '市场报告',
        '洞察', '复盘', '案例', '玩法', '攻略', '方法论', '策略', '分析',
        # 泛商业词：覆盖新闻类订阅源的绝大多数内容
        '品牌', '消费', '消费者', '市场', '行业', '企业', '公司',
        '营收', '财报', '利润', '融资', '收购', '投资',
        '发布', '上线', '合作', '战略', '布局', '动作',
        '趋势', '预测', '洞察', '观察', '数据', '报告',
        '数字化', '转型', '升级', '创新', '变革',
        '节点', '大促', '活动', 'campaign',
        'KOL', '达人', '博主', '网红',
        '内容营销', '私域', '全域', '链路', '闭环',
        '人群', '用户', 'Z世代', '年轻人', '银发',
        '小红书种草', '抖音', '快手', 'B站', '视频号',
        '海外', '出海', '全球化', '跨境',
        '广告收入', '媒体收入', '平台收入'
    ]):
        return '营销增长'

    return '其他'


def infer_value(title, cat):
    """根据标题和分类，补一行业务价值判断"""
    t = (title or '').lower()

    if any(k in t for k in ['发布', '上线', '开源', '推出', '正式']):
        action = '值得关注新动作，适合判断是否要跟进测试。'
    elif any(k in t for k in ['更新', '升级', '优化', '改版']):
        action = '说明平台/工具在迭代，可能影响现有玩法。'
    elif any(k in t for k in ['价格', '收费', '成本', '降价', '涨价']):
        action = '直接影响使用门槛和投放/工具预算。'
    elif any(k in t for k in ['案例', '复盘', '实战', '经验']):
        action = '偏方法论，可提炼成可复用动作。'
    elif any(k in t for k in ['政策', '规则', '治理', '处罚', '整改']):
        action = '偏规则变化，避免踩坑比跟热点更重要。'
    elif any(k in t for k in ['趋势', '报告', '观察', '数据', '财报']):
        action = '偏趋势信号，适合用来校准判断。'
    else:
        action = '有增量信息，值得快速过一眼。'

    cat_hint = {
        '营销+AI': '重点看AI能不能直接提升竞价效率或降低投放成本。',
        '电商零售': '重点看成交链路、转化动作和商品页优化点。',
        '营销增长': '重点看获客成本、投放策略和转化率优化空间。',
        '小红书': '重点看种草逻辑、聚光投放机制和转化路径。',
        '京东': '重点看京东站内投放、联盟政策和商家运营变化。',
        '抖音': '重点看巨量投放、直播转化和素材爆量规律。',
        '阿里妈妈': '重点看直通车/引力魔方出价变化和流量成本。'
    }.get(cat, '重点看它是否改变你现在的决策。')

    return f"为什么值得看：{action}{cat_hint}"


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

    # 加载全部来源
    sources = load_sources_from_opml()
    print(f"加载了 {len(sources)} 个公众号来源")

    # 并行抓取全部
    all_items = fetch_all_feeds_parallel(sources, yesterday_date, yesterday, max_workers=5)

    # 近7天去重，只保留增量
    history_items = load_dedup_history()
    selected_source_count = len(all_items)
    all_items, dropped_items, _ = deduplicate_items(all_items, history_items, yesterday)
    print(f"增量过滤：原始 {selected_source_count} 条，过滤重复 {len(dropped_items)} 条，保留新增 {len(all_items)} 条")

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

    # 目标数量：竞价+电商为主，AI为辅
    TARGET_COUNTS = {
        '营销增长': 14,   # 竞价/效果广告/投放策略（最优先）
        '电商零售': 12,   # 国内电商转化/GMV/直播带货
        '阿里妈妈': 5,    # 淘系+拼多多竞价投放
        '抖音': 4,        # 抖音电商/巨量投放
        '小红书': 4,      # 小红书种草/聚光投放
        '京东': 3,        # 京东商家/京东联盟
        '营销+AI': 4      # AI辅助投放工具为主，减少泛AI
    }

    # 精选内容
    selected_items = []
    for cat, target in TARGET_COUNTS.items():
        items = cats.get(cat, [])
        selected_items.extend(items[:target])

    # 如果还不够46条，从其他分类补充（放宽：只要不是'其他'就加入）
    if len(selected_items) < 46:
        remaining = 46 - len(selected_items)
        for item in other_items[:remaining]:
            item['cat'] = classify(item['title'])
            if item['cat'] != '其他':
                selected_items.append(item)

    # 重新按分类组织
    selected_cats = {cat: [] for cat in CAT_EMOJI.keys()}
    for item in selected_items:
        if item['cat'] in selected_cats:
            selected_cats[item['cat']].append(item)

    today_str = datetime.now().strftime('%Y年%m月%d日')

    if not selected_items:
        content = (
            f"📰 微信公众号精选摘要 | {today_str}\n"
            f"（昨日{yesterday}内容）\n\n"
            f"今天没有值得新增同步的内容。\n"
            f"近{DEDUP_DAYS}天重复内容已自动过滤：{len(dropped_items)}条。\n"
        )
    else:
        content = (
            f"📰 微信公众号精选摘要 | {today_str}\n"
            f"（昨日{yesterday}内容，新增{len(selected_items)}条）\n"
            f"已过滤近{DEDUP_DAYS}天重复内容：{len(dropped_items)}条\n\n"
        )

        for cat in CAT_EMOJI.keys():
            items = selected_cats[cat]
            if not items:
                continue
            emoji = CAT_EMOJI[cat]
            content += f"\n{emoji} {cat} ({len(items)}条)\n"
            for item in items:
                content += f"{item['title']}\n{infer_value(item['title'], item['cat'])}\n{item['link']}\n"

    # 保存去重历史（只记录实际发送出去的 selected_items）
    sent_history = history_items + [
        {
            'date': yesterday,
            'title': item.get('title', ''),
            'link': item.get('link', ''),
            'fingerprint': title_fingerprint(item.get('title', '')),
            'cat': item.get('cat', ''),
            'source': item.get('source', '')
        }
        for item in selected_items
    ]
    save_dedup_history(sent_history)

    doc_title = f"每日精选资讯 | {today_str}"

    # 创建文档（输出内容供 Agent 使用 feishu_create_doc 写入）
    doc_title, doc_url, content = create_feishu_doc(doc_title, content)

    print(f"\n✅ 脚本执行完成")
    print(f"请使用 feishu_create_doc 工具创建飞书文档，标题: {doc_title}")
    print(f"内容见上方 FEISHU_CONTENT 标记")




if __name__ == '__main__':
    main()

