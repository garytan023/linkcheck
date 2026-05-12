#!/usr/bin/env python3
"""
每日微信公众号资讯同步 v4
基于 v2 的完整结构（45源 + 去重 + 飞书文档/Discord输出）
+ AI 理解意图后评分/分类（替代关键词分类）

AI 分类策略：
- 并行抓取完成后，一次性把所有文章 batch 发给 AI
- AI 返回每个文章的优化分类 + 评分 + 是否推荐入选
- 关键词分类作为 fallback 和参考基准
- 分类优先级：京东 > 阿里妈妈 > 抖音 > 小红书 > 营销+AI > 电商零售 > 营销增长 > 其他
"""
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import json
import os
import sys
import html
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

RSS_SERVER = 'http://s.ztso.xyz:11211/feed'
OPML_FILE = os.path.expanduser('~/.openclaw/workspace-dev/data/wechat_rss_subscriptions.opml')
CHECKPOINT_FILE = os.path.expanduser('~/.openclaw/workspace-dev/data/daily_news_checkpoint.json')
DEDUP_HISTORY_FILE = os.path.expanduser('~/.openclaw/workspace-dev/data/daily_news_dedup_history.json')
DEDUP_DAYS = 7
OUTPUT_DIR = os.path.expanduser('~/.openclaw/workspace-dev/output')
OPENCLAW_CONFIG = os.path.expanduser('~/.openclaw/openclaw.json')
NOTION_PAGE_ID = '31cdb0fc025f8141b46afcd7976c3537'


def load_runtime_config():
    env = {
        'TWELVEAI_API_KEY': os.environ.get('TWELVEAI_API_KEY', ''),
        'LLHUBOPEN_API_KEY': os.environ.get('LLHUBOPEN_API_KEY', ''),
        'CLIPROXY_API_KEY': os.environ.get('CLIPROXY_API_KEY', ''),
        'DISCORD_BOT_TOKEN': os.environ.get('DISCORD_BOT_TOKEN', ''),
        'FEISHU_APP_ID': os.environ.get('FEISHU_APP_ID', ''),
        'FEISHU_APP_SECRET': os.environ.get('FEISHU_APP_SECRET', ''),
        'NOTION_KEY': os.environ.get('NOTION_KEY', ''),
    }

    try:
        cfg = json.loads(Path(OPENCLAW_CONFIG).read_text(encoding='utf-8'))
    except Exception:
        cfg = {}

    if not env['TWELVEAI_API_KEY']:
        env['TWELVEAI_API_KEY'] = (((cfg.get('models') or {}).get('providers') or {}).get('12ai') or {}).get('apiKey', '')
    if not env['LLHUBOPEN_API_KEY']:
        env['LLHUBOPEN_API_KEY'] = (((cfg.get('models') or {}).get('providers') or {}).get('llhubopen') or {}).get('apiKey', '')
    if not env.get('CLIPROXY_API_KEY'):
        env['CLIPROXY_API_KEY'] = (((cfg.get('models') or {}).get('providers') or {}).get('cliproxy') or {}).get('apiKey', '')
    if not env['DISCORD_BOT_TOKEN']:
        env['DISCORD_BOT_TOKEN'] = (((cfg.get('channels') or {}).get('discord') or {}).get('token', ''))
    if not env['FEISHU_APP_ID']:
        env['FEISHU_APP_ID'] = (((((cfg.get('channels') or {}).get('feishu') or {}).get('accounts') or {}).get('xiaofeng') or {}).get('appId', ''))
    if not env['FEISHU_APP_SECRET']:
        env['FEISHU_APP_SECRET'] = (((((cfg.get('channels') or {}).get('feishu') or {}).get('accounts') or {}).get('xiaofeng') or {}).get('appSecret', ''))
    if not env['NOTION_KEY']:
        env['NOTION_KEY'] = ((((cfg.get('skills') or {}).get('entries') or {}).get('notion') or {}).get('apiKey', ''))

    return env


RUNTIME = load_runtime_config()

# AI API 配置（使用 cliproxy 本地代理 deepseek-v4-flash，稳定快速）
AI_API_URL = 'http://127.0.0.1:8317/v1/chat/completions'
AI_API_KEY = RUNTIME.get('CLIPROXY_API_KEY', '')
AI_MODEL = 'deepseek-v4-flash'

# Discord channel ID
DISCORD_CHANNEL_ID = '1478997781187268608'
# Discord bot token
DISCORD_BOT_TOKEN = RUNTIME.get('DISCORD_BOT_TOKEN', '')

# 飞书配置
FEISHU_APP_ID = RUNTIME.get('FEISHU_APP_ID', '')
FEISHU_APP_SECRET = RUNTIME.get('FEISHU_APP_SECRET', '')
FEISHU_USER_OPENID = 'ou_d635f4f3d20ac474cf8575038b5d2b33'
NOTION_KEY = RUNTIME.get('NOTION_KEY', '')

# v2 原始分类 + 其他
CAT_EMOJI = {
    '京东': '🟣', '字节': '🔵', '阿里妈妈': '🟠', '小红书': '🔴',
    '腾讯': '🟢', '百度': '⚪', '电商零售': '🛒', '营销增长': '📈',
    '营销+AI': '🤖', '其他': '📌'
}
CAT_ORDER = ['京东', '字节', '阿里妈妈', '小红书', '腾讯', '百度', '电商零售', '营销增长', '营销+AI', '其他']

# 目标数量（v2 原始）
TARGET_COUNTS = {
    '营销增长': 14,
    '电商零售': 12,
    '阿里妈妈': 5,
    '抖音': 4,
    '小红书': 4,
    '京东': 3,
    '营销+AI': 4,
    '其他': 4,
}

_session = None
_seen_lock = threading.Lock()


def is_noise(title):
    """识别广告软文 / 招聘内容 / 活动营销，排除噪音"""
    t = (title or '')
    lower_t = t.lower()

    # ========== 严格过滤：招聘类 ==========
    hiring_kw = ['诚聘', '招聘', '急招', '加入我们', '猎头', 'hr诚聘', '高薪诚聘',
                 '薪资面议', '跳槽', 'offer直达', 'offer', '面试', '入职', '简历投递',
                 '简历', '内推', '全职', '兼职', '实习', '岗位', '职位', '招人',
                 '【诚聘】', '【招聘】', '【急招】']
    if any(k in t for k in hiring_kw):
        return True

    # ========== 严格过滤：活动/会议/峰会/交流类 ==========
    event_kw = ['峰会', '论坛', '沙龙', '大会', '交流会', '分享会', '研讨会', '闭门会',
                '圆桌', '活动', '报名', '扫码', '席位', '门票', '参会', '到场',
                '现场', '线下', '直播预约', '预约报名', '名额有限', '先到先得',
                '亿级卖家', '赋能会', '招商会', '发布会', '答谢会', '周年庆',
                '【活动】', '【峰会】', '【大会】', '【沙龙】', '【论坛】']
    if any(k in t for k in event_kw):
        return True

    # ========== 严格过滤：促销/广告类 ==========
    promo_kw = ['免费领', '限时抢', '立即购买', '优惠码', '满减', '0元购', '1元购',
                '惊喜价', '优惠价', '全网首发', '限时优惠', '0门槛', '福利', '特价',
                '特惠', '秒杀', '折扣', '优惠', '大促', '618', '双11', '双十一',
                '双12', '双十二', '年货节', '品牌日', '超级品牌日']
    if any(k in t for k in promo_kw):
        return True

    # ========== 严格过滤：转发/互动类 ==========
    social_kw = ['转给朋友', '扩散', '建议收藏', '朋友圈', '求求了', '救命',
                 '转发', '分享', '在看', '点赞', '评论', '收藏', '转发给']
    if any(k in t for k in social_kw):
        return True

    # ========== 严格过滤：纯工具/介绍类 ==========
    tool_kw = ['功能上线', '功能更新', '产品更新', '版本更新', '系统升级', '新功能',
               '操作指南', '使用说明', '新手入门', '入门教程', '产品手册']
    if any(k in t for k in tool_kw):
        return True

    # ========== 严格过滤：海外平台 ==========
    foreign_kw = ['meta', 'facebook', '亚马逊', 'amazon', 'tiktok', 'youtube',
                  'google', 'instagram', 'snapchat', 'twitter', 'linkedin']
    if any(k in lower_t for k in foreign_kw):
        return True

    return False


def normalize_text(text):
    if not text:
        return ''
    t = text.strip().lower()
    for ch in ['【', '】', '[', ']', '（', '）', '(', ')', '｜', '|', '：', ':', '，', ',', '。', '.', '！', '!', '？', '?', '"', '"', "'", '、', '/', '-', '_']:
        t = t.replace(ch, ' ')
    return ' '.join(t.split())


def title_fingerprint(title):
    normalized = normalize_text(title)
    tokens = [tok for tok in normalized.split() if len(tok) > 1]
    return ' '.join(tokens[:12])


def load_dedup_history():
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
        if link and link in seen_links:
            is_dup = True
        elif title and title in seen_titles:
            is_dup = True
        elif fp and fp in seen_fingerprints:
            is_dup = True
        if is_dup:
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
    global _session
    if _session is None:
        s = requests.Session()
        retry = Retry(total=2, connect=2, read=2, backoff_factor=0.8,
                      status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["GET", "POST"])
        adapter = HTTPAdapter(max_retries=retry, pool_connections=20, pool_maxsize=20)
        s.mount('http://', adapter)
        s.mount('https://', adapter)
        s.headers.update({'User-Agent': 'daily-news-sync/v4'})
        _session = s
    return _session


def load_sources_from_opml():
    try:
        tree = ET.parse(OPML_FILE)
        root = tree.getroot()
        sources = []
        for outline in root.findall('.//outline'):
            title = outline.get('title', '')
            xml_url = outline.get('xmlUrl', '')
            if xml_url and 'MP_WXS_' in xml_url:
                sid = xml_url.split('/')[-1].replace('.atom', '')
                sources.append({'id': sid, 'name': title})
        return sources
    except Exception as e:
        print(f"Error loading OPML: {e}")
        return []


def parse_feed(sid, name):
    url = f'{RSS_SERVER}/{sid}.atom'
    try:
        resp = get_session().get(url, timeout=(4, 10))
        if resp.status_code != 200:
            print(f"[WARN] {name} status={resp.status_code}")
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
                # 提取摘要（用于 AI 评分）
                summary = entry.find('atom:summary', ns)
                content = entry.find('atom:content', ns)
                summary_text = ''
                if content is not None and content.text:
                    summary_text = html.unescape(content.text)[:500]
                elif summary is not None and summary.text:
                    summary_text = html.unescape(summary.text)[:500]
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
        print(f"[ERR] {name}: {type(e).__name__}: {e}")
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
    def json_serializer(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    with open(CHECKPOINT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=json_serializer)


def fetch_all_feeds_parallel(sources, yesterday_date, yesterday, max_workers=5):
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
                    if is_noise(title):
                        continue
                    with _seen_lock:
                        if title in seen:
                            continue
                        seen.add(title)
                    cat = keyword_classify(title)  # 关键词预分类，AI 之后会重评
                    result.append({
                        'title': title,
                        'link': item['link'],
                        'cat': cat,
                        'source': item['source'],
                        'date': item['date'],
                        'summary': item.get('summary', '')
                    })
        return name, matched, result, len(items)

    print(f"并行抓取 {len(sources)} 个来源 (并发数: {max_workers})...")
    save_checkpoint(yesterday, 0, len(sources), stats, all_items)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_one, src): src for src in sources}
        completed = 0
        for future in as_completed(futures):
            completed += 1
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
                print(f"  [{completed:02d}/{len(sources)}] FAILED: {type(e).__name__}: {e}")
            save_checkpoint(yesterday, completed, len(sources), stats, all_items)

    print(f"抓取完成，共 {len(all_items)} 条昨日资讯 | ok={stats['ok']} empty={stats['empty']} failed={stats['failed']}")
    return all_items


def keyword_classify(title):
    """关键词预分类 - v2 原始分类逻辑，AI 会重评"""
    t = title
    tl = t.lower()

    # 营销+AI（严格：必须是AI应用于投放/营销工具的场景）
    # 用更精准的组合词，避免误杀电商零售/平台新闻
    ai_marketing_kw = ['ai营销', 'ai广告', 'aigc', 'ai内容营销', 'ai生成', 'ai创作',
                        'ai辅助投放', 'ai智能投放', 'ai投放工具', 'ai广告工具',
                        'ai种草', 'ai内容生成', 'ai文案', 'ai素材',
                        '智能广告', '智能投放', '大模型营销', '大模型投放',
                        'agent营销', 'agent投放', 'gpt营销', 'kimi营销',
                        'deepseek营销', '通义营销', '文心营销', '豆包营销']
    if any(k in tl for k in ['gpt', 'kimi', 'deepseek', '文心', '通义', '豆包', 'minimax',
                               'aigc', 'openai', 'openclaw', '人工智能', '大模型应用']):
        return '营销+AI'
    # 精准组合词才认
    if any(k in tl for k in ai_marketing_kw):
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

    # 营销增长
    if any(k in tl for k in ['竞价', '付费媒体', '付费流量', '信息流', '效果广告', '投放', '投放策略', '投放案例', '投放复盘', '投放优化', '投放成本', '广告投放', '广告案例', '广告优化', '广告策略', '广告主', 'ocpx', '智能定向', '人群定向', '出价', '起量', '放量', '压成本', '降本', '营销', '增长', '获客', '转化', '私域', '品牌广告', '效果营销', '广告平台', '行业报告', '营销报告', '营销趋势', '趋势报告', '数据报告', '市场报告', '洞察', '复盘', '案例', '玩法', '攻略', '方法论', '策略', '分析', '品牌', '消费', '消费者', '市场', '行业', '企业', '公司', '营收', '财报', '利润', '融资', '收购', '投资', '发布', '上线', '合作', '战略', '布局', '动作', '趋势', '预测', '观察', '数据', '报告', '数字化', '转型', '升级', '创新', '变革', '节点', '大促', '活动', 'campaign', 'KOL', '达人', '博主', '网红', '内容营销', '全域', '链路', '闭环', '人群', '用户', 'Z世代', '年轻人', '银发', '海外', '出海', '全球化', '跨境', '广告收入', '媒体收入', '平台收入']):
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


def batch_ai_classify(articles, max_tokens=8000):
    """
    批量 AI 分类与评分（v2 - 带摘要理解）
    AI 先阅读每篇文章的标题+摘要，从多维度理解内容深度后，再给出分数
    为避免API超时，将文章分批发送（每批最多25篇）
    """
    if not articles:
        return {}

    # 分批处理（每批最多25篇，避免 API 超时）
    BATCH_SIZE = 25
    all_results = {}
    total_batches = (len(articles) + BATCH_SIZE - 1) // BATCH_SIZE

    for batch_idx in range(total_batches):
        start = batch_idx * BATCH_SIZE
        end = min(start + BATCH_SIZE, len(articles))
        batch = articles[start:end]

        article_list = []
        for i, art in enumerate(batch):
            global_idx = start + i
            summary = (art.get('summary') or '')[:150]
            article_list.append(
                f"[{global_idx}] 标题：{art['title']}\n"
                f"    摘要：{summary}\n"
                f"    来源：{art['source']}\n"
                f"    预分类：{art.get('cat', '其他')}"
            )

        prompt = f"""你是一个专注于国内竞价媒体与电商的资讯评分专家。

## 任务
阅读以下每篇文章的【标题+摘要】，从多个维度理解内容后，给出：
1. 准确的分类（cat）
2. 综合评分（score, 0-10）
3. 是否推荐入选（recommend）
4. 评分理由（reason，一句话说明评分理由）

## 分类定义（严格优先级：京东/阿里妈妈/小红书/抖音/腾讯/百度 > 电商零售 > 营销+AI > 营销增长 > 其他）
- 京东：京东站内投放、京准通、京东联盟、京东商家运营
- 抖音：抖音/巨量引擎/巨量千川、字节系营销、抖音电商
- 阿里妈妈：淘系广告（直通车、引力魔方、万相台、达摩盘等）
- 小红书：小红书种草、聚光投放、小红书商家运营
- 腾讯：腾讯广告、微信生态营销
- 百度：百度营销、百度竞价
- 电商零售：电商运营、直播带货、品牌零售、电商转化链路
- 营销+AI：AI辅助投放（AIGC素材、智能出价、大模型营销工具），注意：仅限有实操价值的AI营销方法
- 营销增长：竞价广告、信息流、投放策略、营销案例、行业报告（以上不包含的泛商业内容）
- 其他：不属于以上

## 评分体系（5个维度，加权求和，最高10分）

### 维度1：媒介竞价投放价值（核心加权，最高4分）
评估文章是否涉及竞价投放实操经验。0分→2分→4分

### 维度2：电商投放内容价值（次要加权，最高3分）
评估文章是否涉及电商投放实战。0分→1.5分→3分

### 维度3：案例与商业模式价值（最高2分）
评估文章是否有可复用的案例/模式。0分→1分→2分

### 维度4：AI营销价值（辅助维度，最高1分）
评估文章的AI营销实操价值。有实测对比/方法=1分，泛泛而谈=0分

### 维度5：内容质量（最高1分）
有数据/案例=1分，否则=0分

### 降权/惩罚
- 海外平台内容（Meta/TikTok/Amazon等）→ -2分
- 泛泛而谈无实质内容 → -1分

## 评分步骤
第1步：读标题+摘要，理解核心
第2步：按5个维度分别打分
第3步：加权求和（维度1 + 维度2×0.75 + 维度3×0.5 + 维度4×0.25 + 维度5×0.1）
第4步：score ≥ 5 → recommend=true，否则 false

## 输出格式
返回 JSON 对象，key 是文章序号，value 是：
{{"cat": "分类名", "score": 0-10整数, "recommend": true/false, "reason": "评分理由"}}

## 注意
- 只返回 JSON，不要其他内容
- score ≥ 5 才 recommend=true

## 文章列表
"""
        for item in article_list:
            prompt += item + "\n"

        try:
            headers = {
                'Authorization': f'Bearer {AI_API_KEY}',
                'Content-Type': 'application/json'
            }
            payload = {
                'model': AI_MODEL,
                'messages': [
                    {'role': 'system', 'content': '你是一个专业的国内竞价媒体与电商资讯分类助手，只返回JSON格式结果。'},
                    {'role': 'user', 'content': prompt}
                ],
                'max_tokens': max_tokens,
                'temperature': 0.1
            }
            resp = requests.post(AI_API_URL, headers=headers, json=payload, timeout=180)
            if resp.status_code != 200:
                print(f"[WARN] 批次{batch_idx+1}/{total_batches} AI error: {resp.status_code}")
                continue

            result_text = resp.json()['choices'][0]['message']['content'].strip()
            import re
            json_match = re.search(r'\{[\s\S]*\}', result_text)
            if json_match:
                batch_result = json.loads(json_match.group())
                all_results.update(batch_result)
                print(f"[AI] 批次{batch_idx+1}/{total_batches} 评分完成: {len(batch_result)} 篇")
            else:
                print(f"[WARN] 批次{batch_idx+1}/{total_batches} 非JSON响应: {result_text[:100]}")
        except Exception as e:
            print(f"[ERR] 批次{batch_idx+1}/{total_batches} AI失败: {type(e).__name__}: {str(e)[:80]}")

    total_ok = len(all_results)
    if total_ok > 0:
        print(f"[AI] 全部完成: {total_ok}/{len(articles)} 篇评分成功")
    else:
        print("[AI] 所有批次均失败")
    return all_results


def select_articles(articles, ai_results):
    """
    精选文章：
    1. 有 AI 结果 → 用 AI 分类和评分
    2. 无 AI 结果 → 用关键词分类和默认评分
    3. 按分类目标数量约束
    4. 分类内按分数降序
    """
    scored = []
    for i, art in enumerate(articles):
        ai_data = ai_results.get(str(i), {})
        if ai_data:
            cat = ai_data.get('cat', art.get('cat', '其他'))
            score = ai_data.get('score', 5)
            recommend = ai_data.get('recommend', True)
            ai_reason = ai_data.get('reason', '')
        else:
            cat = art.get('cat', '其他')
            score = 5
            recommend = True
            ai_reason = '（关键词 fallback）'

        # 验证分类合法性
        if cat not in CAT_ORDER:
            cat = '其他'

        scored.append({
            **art,
            'cat': cat,
            'score': score,
            'recommend': recommend,
            'ai_reason': ai_reason,
            'ai_override': bool(ai_data)
        })

    # 按推荐 + 分数排序
    scored.sort(key=lambda x: (x['recommend'], x['score']), reverse=True)

    # 按分类目标数量选取
    selected = []
    cat_counts = {cat: 0 for cat in CAT_ORDER}
    for art in scored:
        cat = art['cat']
        target = TARGET_COUNTS.get(cat, 3)
        if cat_counts[cat] < target:
            selected.append(art)
            cat_counts[cat] += 1

    return selected


def get_feishu_token():
    """获取飞书 tenant_access_token"""
    if not FEISHU_APP_ID or not FEISHU_APP_SECRET:
        print("[Feishu] 缺少 FEISHU_APP_ID / FEISHU_APP_SECRET")
        return None

    url = 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal'
    try:
        resp = requests.post(url, json={'app_id': FEISHU_APP_ID, 'app_secret': FEISHU_APP_SECRET}, timeout=15)
        if resp.status_code != 200:
            print(f"[Feishu] 获取 token 失败: HTTP {resp.status_code} - {resp.text[:200]}")
            return None
        data = resp.json()
        if data.get('code') != 0:
            print(f"[Feishu] 获取 token 失败: {data.get('msg')} ({data.get('code')})")
            return None
        return data.get('tenant_access_token')
    except Exception as e:
        print(f"[Feishu] 获取 token 异常: {type(e).__name__}: {e}")
        return None


def send_feishu_im(token, content, receive_id_type='open_id', receive_id=None):
    """发送飞书 IM 消息给 Gary"""
    if not receive_id:
        receive_id = FEISHU_USER_OPENID
    url = f'https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type={receive_id_type}'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    # 飞书单条消息最大 6000 字符，按需分割
    MAX_LEN = 5800
    chunks = []
    for i in range(0, len(content), MAX_LEN):
        chunks.append(content[i:i+MAX_LEN])

    ok = True
    for idx, chunk in enumerate(chunks):
        payload = {
            'receive_id': receive_id,
            'msg_type': 'text',
            'content': json.dumps({'text': chunk})
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=15)
            result = resp.json()
            if result.get('code') == 0:
                print(f"[Feishu IM] 发送成功 ({idx+1}/{len(chunks)}) ✅")
            else:
                ok = False
                print(f"[Feishu IM] 发送失败: {result.get('msg')} ({result.get('code')})")
        except Exception as e:
            ok = False
            print(f"[Feishu IM] 异常: {type(e).__name__}: {e}")
    return ok


def format_notion_blocks(selected_cats):
    """格式化 Notion blocks"""
    blocks = []
    for cat in CAT_ORDER:
        items = selected_cats.get(cat, [])
        if not items:
            continue
        blocks.append({
            'object': 'block',
            'type': 'heading_2',
            'heading_2': {'rich_text': [{'type': 'text', 'text': {'content': f"{CAT_EMOJI[cat]} {cat}"}}]}
        })
        for idx, item in enumerate(items, 1):
            blocks.append({
                'object': 'block',
                'type': 'paragraph',
                'paragraph': {
                    'rich_text': [{
                        'type': 'text',
                        'text': {
                            'content': f"{idx}. {item['title']}",
                            'link': {'url': item['link']} if item.get('link') else None,
                        }
                    }]
                }
            })
    return blocks


def sync_to_notion(selected_cats):
    """同步到 Notion 页面"""
    if not NOTION_KEY or not NOTION_PAGE_ID:
        print("⚠️ Notion配置未完成，跳过Notion同步")
        return False

    headers = {
        'Authorization': f'Bearer {NOTION_KEY}',
        'Notion-Version': '2025-09-03',
        'Content-Type': 'application/json'
    }
    list_url = f'https://api.notion.com/v1/blocks/{NOTION_PAGE_ID}/children'

    try:
        resp = requests.get(list_url, headers=headers, timeout=20)
        if resp.status_code == 200:
            for bb in resp.json().get('results', [])[:99]:
                requests.delete(f"https://api.notion.com/v1/blocks/{bb['id']}", headers=headers, timeout=20)
        else:
            print(f"[Notion] 读取旧内容失败: {resp.status_code} {resp.text}")
            return False

        blocks = format_notion_blocks(selected_cats)
        if not blocks:
            print("[Notion] 无内容可同步")
            return True

        for i in range(0, len(blocks), 100):
            batch = blocks[i:i+100]
            resp = requests.patch(list_url, headers=headers, json={'children': batch}, timeout=20)
            if resp.status_code != 200:
                print(f"[Notion] 写入失败: {resp.status_code} {resp.text}")
                return False
        print("[Notion] 同步成功 ✅")
        return True
    except Exception as e:
        print(f"[Notion] 异常: {type(e).__name__}: {e}")
        return False


def create_feishu_doc(token, title, articles, yesterday, selected_cats):
    """通过飞书 API 创建文档并写入内容，返回文档 URL"""
    # 1. 创建空白文档
    create_url = 'https://open.feishu.cn/open-apis/docx/v1/documents'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    try:
        resp = requests.post(create_url, headers=headers, json={'title': title}, timeout=15)
        result = resp.json()
        if result.get('code') != 0:
            print(f"[Feishu Doc] 创建失败: {result.get('msg')} ({result.get('code')})")
            return None
        doc_id = result['data']['document']['document_id']
        doc_url = f"https://www.feishu.cn/docx/{doc_id}"
        print(f"[Feishu Doc] 创建成功: {doc_url}")
    except Exception as e:
        print(f"[Feishu Doc] 创建异常: {type(e).__name__}: {e}")
        return None

    # 2. 写入内容（使用 blocks API）
    blocks_url = f'https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children'

    def make_text_block(text):
        """创建一个文本 block（docx children 接口要求 text，不是 paragraph）"""
        return {
            'block_type': 2,
            'text': {
                'elements': [{'text_run': {'content': text}}],
                'style': {}
            }
        }

    blocks = []
    blocks.append(make_text_block(f"📋 每日资讯精选 {yesterday} | 完整{len(articles)}条"))
    blocks.append(make_text_block(' '))

    for cat in CAT_ORDER:
        items = selected_cats.get(cat, [])
        if not items:
            continue
        emoji = CAT_EMOJI[cat]
        blocks.append(make_text_block(f"{emoji} {cat}（{len(items)}条）"))
        for item in items:
            blocks.append(make_text_block(item['title']))
            blocks.append(make_text_block(item['link']))

    try:
        resp = requests.post(blocks_url, headers=headers, json={'children': blocks, 'index': -1}, timeout=30)
        result = resp.json()
        if result.get('code') == 0:
            print(f"[Feishu Doc] 内容写入成功 ✅")
        else:
            print(f"[Feishu Doc] 内容写入失败: {result.get('msg')} ({result.get('code')})")
    except Exception as e:
        print(f"[Feishu Doc] 内容写入异常: {type(e).__name__}: {e}")

    return doc_url


def send_discord(content):
    """发送Discord消息"""
    if not DISCORD_BOT_TOKEN or not DISCORD_CHANNEL_ID:
        print("⚠️ Discord配置未完成，跳过Discord发送")
        return False

    headers = {
        'Authorization': f'Bot {DISCORD_BOT_TOKEN}',
        'Content-Type': 'application/json'
    }

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


def build_feishu_content(articles, yesterday, total_raw, dedup_dropped, selected_cats):
    """构建飞书文档内容（3行/条格式：标题+价值判断+链接）"""
    today_str = datetime.now().strftime('%Y年%m月%d日')

    if not articles:
        content = (
            f"📰 微信公众号精选摘要 | {today_str}\n"
            f"（昨日{yesterday}内容）\n\n"
            f"今天没有值得新增同步的内容。\n"
            f"近{DEDUP_DAYS}天重复内容已自动过滤：{dedup_dropped}条。\n"
        )
    else:
        content = (
            f"📰 微信公众号精选摘要 | {today_str}\n"
            f"（昨日{yesterday}内容，新增{len(articles)}条）\n"
            f"已过滤近{DEDUP_DAYS}天重复内容：{dedup_dropped}条\n\n"
        )

        for cat in CAT_ORDER:
            items = selected_cats.get(cat, [])
            if not items:
                continue
            emoji = CAT_EMOJI[cat]
            content += f"\n{emoji} {cat} ({len(items)}条)\n"
            for item in items:
                content += f"{item['title']}\n{infer_value(item['title'], item['cat'])}\n{item['link']}\n"

    return content


# 平台官方来源映射（用于平台板块）
PLATFORM_SOURCE_MAP = {
    '京东': ['京东黑板报', '京东研究院', '京东云', '京准通'],
    '字节': ['巨量引擎营销观察', '抖音电商营销观察', '巨量算数'],
    '小红书': ['小红书商业动态', '小红书技术REDtech'],
    '阿里妈妈': ['阿里妈妈数字营销', '阿里妈妈万堂书院'],
    '腾讯': ['腾讯广告'],
    '百度': ['百度营销观'],
}

# 平台板块分类 emoji
PLATFORM_EMOJI = {
    '京东': '🟣', '字节': '🔵', '阿里妈妈': '🟠',
    '小红书': '🔴', '腾讯': '🟢', '百度': '⚪'
}

# 公众号精选板块分类 emoji
CURATED_EMOJI = {
    '营销+AI': '🤖', '电商零售': '🛒',
    '营销增长': '📈', '其他': '📌'
}


def build_feishu_im_content(articles, yesterday, selected_cats, doc_url=None):
    """构建飞书 IM 消息内容（平台优先 + 3行详情 + emoji + ⭐评分）"""
    if not articles:
        lines = [
            f"📰 {yesterday} 每日资讯精选",
            f"近{DEDUP_DAYS}天重复内容已自动过滤，今天没有值得新增同步的内容。"
        ]
        if doc_url:
            lines.append(f"📄 飞书文档：{doc_url}")
        return '\n'.join(lines)

    # 分离平台官方文章 vs 公众号精选
    platform_items = {}  # {cat: [items]}
    curated_items = {}

    for cat in CAT_ORDER:
        cat_items = selected_cats.get(cat, [])
        if not cat_items:
            continue
        is_platform_cat = cat in PLATFORM_SOURCE_MAP
        if is_platform_cat:
            platform_keys = PLATFORM_SOURCE_MAP[cat]
            plat_list = [it for it in cat_items if it.get('source', '') in platform_keys]
            cur_list = [it for it in cat_items if it.get('source', '') not in platform_keys]
            if plat_list:
                platform_items[cat] = plat_list
            if cur_list:
                curated_items[cat] = cur_list
        else:
            curated_items[cat] = cat_items

    def fmt_item(item):
        source = item.get('source', '')
        title = item.get('title', '')
        link = item.get('link', '')
        reason = item.get('reason', item.get('summary', ''))[:80]
        score = item.get('score', 0)
        prefix = '⭐' if score >= 8 else ''
        # 构建链接文本：取标题前30字
        short_title = title[:40] if len(title) > 40 else title
        return (
            f"{prefix}{source} | {title}\n"
            f"{reason}\n"
            f"🔗 [{short_title}]({link})"
        )

    lines = [
        f"📰 {yesterday} 每日资讯精选",
        "",
    ]

    # 平台官方资讯板块
    if platform_items:
        lines.append("📱 平台官方资讯（优先展示）")
        lines.append("")
        for cat in CAT_ORDER:
            items = platform_items.get(cat, [])
            if not items:
                continue
            emoji = PLATFORM_EMOJI.get(cat, '📌')
            lines.append(f"{emoji} 【{cat}】")
            for item in items:
                lines.append(fmt_item(item))
                lines.append("")
        lines.append("")

    # 公众号精选板块
    if curated_items:
        lines.append("📋 公众号精选（按评分排序）")
        lines.append("")
        # 按平台分类 + 其他分类的顺序，平台分类排在前面
        curated_order = [c for c in CAT_ORDER if c in curated_items and c in PLATFORM_SOURCE_MAP]
        curated_order += [c for c in CAT_ORDER if c in curated_items and c not in PLATFORM_SOURCE_MAP]
        for cat in curated_order:
            items = curated_items.get(cat, [])
            if not items:
                continue
            # 按评分降序排列
            items_sorted = sorted(items, key=lambda x: x.get('score', 0), reverse=True)
            emoji = CURATED_EMOJI.get(cat, PLATFORM_EMOJI.get(cat, '📌'))
            lines.append(f"{emoji} 【{cat}】")
            for item in items_sorted:
                lines.append(fmt_item(item))
                lines.append("")

    # 统计信息
    plat_total = sum(len(v) for v in platform_items.values())
    cur_total = sum(len(v) for v in curated_items.values())
    all_scores = [it.get('score', 0) for it in articles]
    max_score = max(all_scores) if all_scores else 0
    avg_score = round(sum(all_scores) / len(all_scores), 1) if all_scores else 0
    lines.append(f"📊 今日收录: {len(articles)}篇 | 平台资讯: {plat_total}篇 | 公众号精选: {cur_total}篇")
    lines.append(f"📊 评分区间: 最高{max_score}分 / 平均{avg_score}分")

    return '\n'.join(lines)


def build_discord_content(articles, yesterday, selected_cats):
    """构建 Discord 摘要内容（v2 风格）"""
    today_str = datetime.now().strftime('%Y年%m月%d日')
    if not articles:
        return None

    lines = [f"📰 微信公众号精选 | {today_str}（昨日{yesterday}）\n"]

    for cat in CAT_ORDER:
        items = selected_cats.get(cat, [])
        if not items:
            continue
        emoji = CAT_EMOJI[cat]
        lines.append(f"\n{emoji} **{cat}** ({len(items)}条)")
        for item in items[:3]:  # 每分类最多3条，避免Discord字符超限
            lines.append(f"• {item['title']}")

    return '\n'.join(lines)


def main():
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    yesterday_date = datetime.strptime(yesterday, '%Y-%m-%d').date()

    print(f"=== 每日资讯同步 v4 | {yesterday} ===")

    # 加载全部来源
    sources = load_sources_from_opml()
    print(f"加载了 {len(sources)} 个公众号来源")

    # 并行抓取
    all_items = fetch_all_feeds_parallel(sources, yesterday_date, yesterday, max_workers=5)

    if not all_items:
        print("⚠️ 昨日无内容，可能是 RSS 代理仍有问题")
        content = f"# 每日资讯精选 | {yesterday}（昨日）\n\n> ⚠️ 昨日所有 RSS 源抓取失败，未能获取任何内容。\n"
        output_file = os.path.join(OUTPUT_DIR, f'rss_daily_{yesterday}.md')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"已写入: {output_file}")
        return

    # 近7天去重
    history_items = load_dedup_history()
    raw_count = len(all_items)
    all_items, dropped_items, new_history = deduplicate_items(all_items, history_items, yesterday)
    print(f"增量过滤：原始 {raw_count} 条，去重 {len(dropped_items)} 条，保留新增 {len(all_items)} 条")

    # AI 批量分类
    print("\n[AI] 开始批量分类...")
    ai_results = batch_ai_classify(all_items)

    # 精选
    selected_items = select_articles(all_items, ai_results)
    print(f"精选完成：{len(selected_items)} 条")

    # 按分类组织
    selected_cats = {cat: [] for cat in CAT_ORDER}
    for item in selected_items:
        if item['cat'] in selected_cats:
            selected_cats[item['cat']].append(item)

    # 输出统计
    print("\n各分类条数：")
    for cat in CAT_ORDER:
        cnt = len(selected_cats.get(cat, []))
        if cnt > 0:
            print(f"  {cat}: {cnt} 条")

    today_str = datetime.now().strftime('%Y年%m月%d日')
    doc_title = f"每日精选资讯 | {today_str}"

    # 构建内容
    content = build_feishu_content(selected_items, yesterday, raw_count, len(dropped_items), selected_cats)

    # 保存 markdown 产物
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    markdown_file = os.path.join(OUTPUT_DIR, f'rss_daily_{yesterday}.md')
    with open(markdown_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"\n已写入 Markdown: {markdown_file}")

    # Notion 同步
    print("\n[Notion] 同步页面...")
    notion_ok = sync_to_notion(selected_cats)

    # 飞书发送闭环
    token = get_feishu_token()
    doc_url = None
    feishu_doc_ok = False
    feishu_im_ok = False
    if token:
        print("\n[Feishu Doc] 创建文档...")
        doc_url = create_feishu_doc(token, doc_title, selected_items, yesterday, selected_cats)
        feishu_doc_ok = bool(doc_url)
    else:
        print("[Feishu] 未获取到 token，跳过文档创建和 IM 发送")

    # Discord 摘要
    discord_content = build_discord_content(selected_items, yesterday, selected_cats)
    discord_ok = False
    if discord_content:
        print("\n[Discord] 发送摘要...")
        if send_discord(discord_content):
            print("[Discord] 发送成功 ✅")
            discord_ok = True
        else:
            print("[Discord] 发送失败")

    # 飞书 IM 消息（全部40条，一条消息发出）
    feishu_im_content = build_feishu_im_content(selected_items, yesterday, selected_cats, doc_url=doc_url)
    if token and feishu_im_content:
        print("\n[Feishu IM] 发送消息...")
        feishu_im_ok = send_feishu_im(token, feishu_im_content, receive_id_type='open_id', receive_id=FEISHU_USER_OPENID)

    # 保存去重历史
    save_dedup_history(new_history)

    # 保存 checkpoint
    def json_serializer(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    output_file = os.path.join(OUTPUT_DIR, f'rss_daily_{yesterday}_selected.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'date': yesterday,
            'total_raw': raw_count,
            'total_selected': len(selected_items),
            'doc_title': doc_title,
            'doc_url': doc_url,
            'articles': selected_items
        }, f, ensure_ascii=False, indent=2, default=json_serializer)
    print(f"\n已保存: {output_file}")

    if not notion_ok:
        print("\n❌ Notion 同步失败")
    if not feishu_doc_ok:
        print("❌ 飞书文档创建失败")
    if token and not feishu_im_ok:
        print("❌ 飞书 IM 发送失败")

    print(f"\n✅ 脚本执行完成")

    if not notion_ok or not feishu_doc_ok or (token and not feishu_im_ok):
        sys.exit(1)


if __name__ == '__main__':
    main()
