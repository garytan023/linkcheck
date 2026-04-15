#!/usr/bin/env python3
"""
RSS 精选脚本 v4
- 排他性分类（每篇文章只归一个分类，不重复）
- 带原文链接
- 提取正文中的互动指标（阅读量/在看/评论等显式数据）
- 只输出昨天内容
"""
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import re, html, os, json

OPML_FILE = os.path.expanduser('~/.openclaw/workspace-dev/data/wechat_rss_subscriptions.opml')
TIMEOUT = 12
DEDUP_DAYS = 7
STATE_DIR = os.path.expanduser('~/.openclaw/workspace-dev/state')
CHECKPOINT_FILE = os.path.join(STATE_DIR, 'rss_digest_checkpoint.json')
DEDUP_HISTORY_FILE = os.path.join(STATE_DIR, 'rss_digest_dedup_history.json')
CST = timezone(timedelta(hours=8))
YESTERDAY = datetime.now(CST) - timedelta(days=1)
YD_STR = YESTERDAY.strftime('%Y-%m-%d')
YD_SHORT = YESTERDAY.strftime('%m-%d')
OUTPUT_FILE = os.path.expanduser(f'~/.openclaw/workspace-dev/output/rss_daily_{YD_STR}.md')
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
os.makedirs(STATE_DIR, exist_ok=True)
ATOM_NS = 'http://www.w3.org/2005/Atom'
CONTENT_NS = 'http://purl.org/rss/1.0/modules/content/'

CAT_EMOJI = {
    '京东': '🟣', '字节': '🔵', '小红书': '🔴', '腾讯': '🟢', '百度': '⚪',
    '营销+AI': '🤖', '电商零售': '🛒', '营销增长': '📈'
}
CAT_ORDER = ['京东', '字节', '小红书', '腾讯', '百度', '营销+AI', '电商零售', '营销增长']

# 来源账号 → 平台分类（优先级最高）
SOURCE_PLATFORM_MAP = {
    # 京东
    "京东黑板报": "京东",
    "京准通": "京东",
    "京麦商家中心": "京东",
    "京东研究院": "京东",
    # 字节/抖音/巨量
    "巨量引擎营销观察": "字节",
    "巨量引擎营销科学": "字节",
    "抖音电商营销观察": "字节",
    "巨量引擎": "字节",
    "巨量云图": "字节",
    # 小红书
    "小红书种草学": "小红书",
    "小红书商业动态": "小红书",
    "小红书技术REDtech": "小红书",
    "小红书商业广告": "小红书",
    # 腾讯
    "腾讯广告": "腾讯",
    # 百度
    "百度营销观": "百度",
}


_session = None


def get_session():
    global _session
    if _session is None:
        s = requests.Session()
        retry = Retry(
            total=2,
            connect=2,
            read=2,
            backoff_factor=0.8,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry, pool_connections=20, pool_maxsize=20)
        s.mount('http://', adapter)
        s.mount('https://', adapter)
        s.headers.update({'User-Agent': 'rss-digest/5.0'})
        _session = s
    return _session


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
    cutoff = (datetime.now(CST) - timedelta(days=DEDUP_DAYS)).date()
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
        'updated_at': datetime.now(CST).isoformat(),
        'items': kept,
    }
    with open(DEDUP_HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def save_checkpoint(stage, total_feeds=0, completed_feeds=0, stats=None, item_count=0):
    payload = {
        'date': YD_STR,
        'stage': stage,
        'total_feeds': total_feeds,
        'completed_feeds': completed_feeds,
        'stats': stats or {},
        'item_count': item_count,
        'saved_at': datetime.now(CST).isoformat(),
    }
    with open(CHECKPOINT_FILE, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def tag(local):
    return f'{{{ATOM_NS}}}{local}'

def parse_date(text):
    if not text:
        return None
    text = text.strip()
    # RFC 1123 格式（WeChat RSS 使用），时间戳为 CST 时区
    try:
        dt = datetime.strptime(text[:26], '%a, %d %b %Y %H:%M:%S')
        return dt.replace(tzinfo=CST)
    except:
        # ISO 8601 格式（包含 Z 或 +00:00）
        try:
            dt = datetime.fromisoformat(text.replace('Z', '+00:00'))
            return dt.astimezone(CST)
        except:
            return None

def classify(title, content, source):
    """排他性分类，严格按来源账号归类：
    1. 官方平台账号（SOURCE_PLATFORM_MAP） → 对应平台分类
    2. 其余全部按内容关键词落入 topic 分类（京东/字节/小红书/腾讯/百度严格只收官方账号）
    """
    # 官方平台账号优先 → 进入平台分类（不做任何关键词扩展）
    if source in SOURCE_PLATFORM_MAP:
        return SOURCE_PLATFORM_MAP[source]

    t = (title or '').lower()
    c = ((content or '')[:3000]).lower()
    # topic 关键词（排他）
    if any(k in t or k in c for k in ['ai', '人工智能', 'gpt', '大模型', '自动化', 'aigc', '数字人',
                                       'deepseek', 'chatgpt', '智能投放', 'geo', 'ai营销', 'claude',
                                       'genai', 'llm', 'agent', '智能体', '工作流', 'gpt-4', 'o1', 'o3', 'gemini']):
        return '营销+AI'
    if any(k in t or k in c for k in ['电商', '零售', '直播带货', '天猫', '淘宝', '选品', '跨境',
                                       '亚马逊', 'shopify', '私域', '拼多多', '唯品会', '即时零售',
                                       '货架电商', '跨境电商', '电商平台', '电商运营', '京东', 'jd.com']):
        return '电商零售'
    return '营销增长'

def score_article(title, content):
    t = (title or '').lower()
    c = ((content or '')[:3000]).lower()

    # ★ 满分关键词：直接返回10，不走常规打分
    满分_kw = ['白皮书', '案例拆解', '实战案例', '案例精解', '完整案例', '案例分析',
                '电商白皮书', '行业白皮书', '平台白皮书']
    if any(k in t for k in 满分_kw):
        return 10

    score = 0
    case_kw = ['案例', '实战', '方法论', '数据', 'gmv', 'roi', '转化率', '投放效果',
                '销售额', '增长', '操盘', '策略', '复盘', '分析报告', '洞察', '拆解',
                '全链路', '种草', '收割', '同比增长', '突破', '暴跌', '首破', '新高',
                '周报', '周刊', '月报', '季报', '年报', '榜单', '趋势', '报告']
    score += min(3, sum(1 for k in case_kw if k in t or k in c))
    media_kw = ['投放', '广告', '信息流', '关键词', '出价', '预算', '竞价', 'cpm', 'cpc',
                'ocpm', '达播', '品牌自播', '投放策略', '代理商', '媒介', '广告主']
    score += min(2, sum(1 for k in media_kw if k in t or k in c))
    ec_kw = ['电商', '零售', '选品', '供应链', '直播带货', '天猫', '淘宝', '跨境',
             '亚马逊', 'shopify', '私域', '复购', '客单价', '电商平台', '拼多多',
             '京东', '外卖', '即时零售', '货架电商']
    score += min(2, sum(1 for k in ec_kw if k in t or k in c))
    ai_kw = ['ai', '人工智能', 'gpt', '大模型', '自动化', 'aigc', '数字人',
              '智能投放', 'geo', 'ai营销', 'deepseek', 'claude', 'chatgpt',
              'genai', 'llm', 'agent', '智能体', '工作流']
    score += min(2, sum(1 for k in ai_kw if k in t or k in c))
    if len(content or '') > 500 and '。' in c:
        score += 1
    # 噪音惩罚
    noise_kw = ['被抓', '被调查', '震惊', '热招', '招聘', '亿级卖家交流会', '峰会', '论坛',
                 '沙龙', '活动报名', '扫码抢位', '席位紧张', '免费领取', '限时报名',
                 '转发', '收藏', '点在看', '阅读原文']
    score -= sum(2 for k in noise_kw if k in t)
    # 低质指标惩罚
    if any(k in t for k in ['马斯克', '特朗普', '普京', '拜登', '关税']):
        score -= 1
    if title and len(title) < 12:
        score -= 1
    return max(0, score)

def is_noise(title):
    t = (title or '')
    noise = ['招聘', '诚聘', '猎头', '免费领', '限时抢', '立即购买', '优惠码',
             '满减', '0元', '转给朋友', '扩散', '建议收藏', '朋友圈', '求职']
    return any(k in t for k in noise)

def normalize_text(text):
    if not text:
        return ''
    t = text.strip().lower()
    for ch in '【】[]（）()｜|:：,,。.!！？?""\'\'、、/-_':
        t = t.replace(ch, ' ')
    return ' '.join(t.split())

def title_fp(title):
    tokens = [tok for tok in normalize_text(title).split() if len(tok) > 1]
    return ' '.join(tokens[:12])

def parse_feed(feed_url, feed_title):
    try:
        r = get_session().get(feed_url, timeout=(4, TIMEOUT))
        r.encoding = 'utf-8'
        if r.status_code != 200:
            print(f"[WARN] {feed_title} status={r.status_code} url={feed_url}")
            return []
        root = ET.fromstring(r.text)
        items = []
        for entry in root.findall('.//' + tag('entry')):
            title_el = entry.find(tag('title'))
            link_el = entry.find(tag('link'))
            published_el = entry.find(tag('published'))
            updated_el = entry.find(tag('updated'))
            content_el = entry.find(f'{{{CONTENT_NS}}}encoded')
            title = html.unescape(title_el.text or '') if title_el is not None else ''
            link = (link_el.get('href') or '') if link_el is not None else ''
            # 优先用 <published>（文章发布时间），其次 <updated>（feed 更新时刻）
            date_text = (published_el.text if published_el is not None else None) or (updated_el.text if updated_el is not None else None)
            pub = parse_date(date_text) if date_text else None
            content = html.unescape(content_el.text) if content_el is not None and content_el.text else ''
            if not title or not link:
                continue
            items.append({'title': title, 'link': link, 'pub': pub, 'source': feed_title, 'content': content})
        return items
    except Exception as e:
        print(f"[ERR] {feed_title} err={type(e).__name__}: {e}")
        return []

def extract_plain_text(html_content):
    if not html_content:
        return ''
    try:
        text = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', '', text)
        text = html.unescape(text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:3000]
    except:
        return ''

def extract_engagement(text):
    """从正文中提取显式的互动指标"""
    result = {}
    if not text:
        return result
    t = text[:6000]
    # 阅读量：优先找"阅读10万+"、"阅读量：100万+"等格式
    m = re.search(r'阅读[量数：:]*\\s*([\\d十百千万余\\.]+万\\+?)', t)
    if m:
        result['阅读量'] = m.group(1)
    m = re.search(r'([\\d\\.]+万\\+?)\\+?\\s*(?:阅读|浏览)', t)
    if m and '阅读量' not in result:
        result['阅读量'] = m.group(1)
    # 在看/点赞
    m = re.search(r'在看[：:]*\\s*([\\d十百千万余\\.]+万\\+?)', t)
    if m:
        result['在看'] = m.group(1)
    # 评论
    m = re.search(r'评论[数：:]*\\s*([\\d十百千万余\\.]+万\\+?)', t)
    if m:
        result['评论'] = m.group(1)
    m = re.search(r'([\\d\\.]+万\\+?)\\s*(?:评论|留言)', t)
    if m and '评论' not in result:
        result['评论'] = m.group(1)
    # 转发
    m = re.search(r'转发[量：:]*\\s*([\\d十百千万余\\.]+万\\+?)', t)
    if m:
        result['转发'] = m.group(1)
    return result

def first_sentence(text, max_len=120):
    """提取第一句有意义的正文"""
    if not text:
        return ''
    # 跳过开头常见噪音（导航、版权、摘要等）
    skip_prefixes = ['来源', '作者', '未经授权', '转载', 'copyright', '©', '相关阅读',
                     '点击', '关注', '扫描', '二维码', '免责声明', '广告', '推广']
    sentences = re.findall(r'[^。！？.!?]{20,150}[。！？.!?]', text)
    for s in sentences:
        lower_s = s.lower()
        if not any(s.lower().startswith(p.lower()) for p in skip_prefixes):
            return s[:max_len]
    return (text[:max_len] + '…') if len(text) > max_len else text

# === 主流程 ===
print("Step 1: 解析 OPML...")
tree = ET.parse(OPML_FILE)
feeds = [(o.get('xmlUrl'), o.get('title', '')) for o in tree.getroot().findall('.//outline[@xmlUrl]')]
print(f"  共 {len(feeds)} 个 RSS 源")

print("Step 2: 并行抓取 feeds...")
all_items = []
seen_fp = set()
stats = {'ok': 0, 'empty': 0, 'failed': 0}
save_checkpoint(stage='fetching', total_feeds=len(feeds), completed_feeds=0, stats=stats, item_count=0)

with ThreadPoolExecutor(max_workers=10) as ex:
    futures = {ex.submit(parse_feed, url, title): (url, title) for url, title in feeds}
    for i, future in enumerate(as_completed(futures)):
        url, title = futures[future]
        try:
            feed_items = future.result()
            if not feed_items:
                stats['empty'] += 1
            else:
                stats['ok'] += 1
            for item in feed_items:
                fp = title_fp(item['title'])
                if fp and fp not in seen_fp and not is_noise(item['title']):
                    seen_fp.add(fp)
                    all_items.append(item)
        except Exception as e:
            stats['failed'] += 1
            print(f"[ERR] {title} future err={type(e).__name__}: {e}")
        save_checkpoint(stage='fetching', total_feeds=len(feeds), completed_feeds=i + 1, stats=stats, item_count=len(all_items))
        if (i+1) % 10 == 0:
            print(f"  {i+1}/{len(feeds)}")

print(f"  去重后: {len(all_items)} 条")

# 只保留昨天
yd_start = datetime(YESTERDAY.year, YESTERDAY.month, YESTERDAY.day, 0, 0, 0, tzinfo=CST)
yd_end = datetime(YESTERDAY.year, YESTERDAY.month, YESTERDAY.day, 23, 59, 59, tzinfo=CST)
recent = [it for it in all_items if it['pub'] and yd_start <= it['pub'] <= yd_end]
print(f"  昨天 {YD_SHORT}: {len(recent)} 条")

# 排他性分类 + 打分 + 正文提取 + 互动指标
seen_links = set()  # 额外去重：同链接只保留一条
for it in recent:
    plain = extract_plain_text(it['content'])
    it['text'] = plain
    it['score'] = score_article(it['title'], plain)
    it['cat'] = classify(it['title'], plain, it['source'])
    it['engagement'] = extract_engagement(plain)

# 再次去重（排他性分类后，同链接不重复）
deduped = []
for it in recent:
    if it['link'] not in seen_links:
        seen_links.add(it['link'])
        deduped.append(it)

recent = deduped
print(f"  排他分类+去重后: {len(recent)} 条")

# 跨天历史去重
history_items = load_dedup_history()
seen_links_hist = set()
seen_titles_hist = set()
seen_fp_hist = set()
for hist in history_items:
    link = (hist.get('link') or '').strip()
    title = (hist.get('title') or '').strip()
    fp = hist.get('fingerprint') or title_fp(title)
    if link:
        seen_links_hist.add(link)
    if title:
        seen_titles_hist.add(title)
    if fp:
        seen_fp_hist.add(fp)

cross_day_dropped = 0
cross_day_recent = []
for it in recent:
    link = (it.get('link') or '').strip()
    title = (it.get('title') or '').strip()
    fp = title_fp(title)
    pub = it.get('pub')
    pub_date = pub.strftime('%Y-%m-%d') if pub else ''

    matched_same_day = False
    if link:
        for hist in history_items:
            if hist.get('link') == link and hist.get('date') == pub_date:
                matched_same_day = True
                break

    if matched_same_day:
        cross_day_recent.append(it)
        continue

    if (link and link in seen_links_hist) or (title and title in seen_titles_hist) or (fp and fp in seen_fp_hist):
        cross_day_dropped += 1
        continue
    cross_day_recent.append(it)
    if link:
        seen_links_hist.add(link)
    if title:
        seen_titles_hist.add(title)
    if fp:
        seen_fp_hist.add(fp)

recent = cross_day_recent
print(f"  跨{DEDUP_DAYS}天去重后: {len(recent)} 条 (过滤 {cross_day_dropped} 条)")
save_checkpoint(stage='deduped', total_feeds=len(feeds), completed_feeds=len(feeds), stats=stats, item_count=len(recent))

# 按分类分组，分类内按分数降序，每分类最多8条
by_cat = defaultdict(list)
for it in recent:
    by_cat[it['cat']].append(it)
for cat in by_cat:
    by_cat[cat].sort(key=lambda x: x['score'], reverse=True)

print("\n各分类条数：")
for cat in CAT_ORDER:
    if cat not in by_cat:
        continue
    items = by_cat[cat]
    top = items[0]['score'] if items else 0
    print(f"  {cat}: {len(items)} 条 (最高分: {top})")

# 生成 Markdown
lines = [
    f'# 每日资讯精选 | {YD_STR}（昨日）\n',
    f"\n> 共抓取 **{len(all_items)}** 条 \\| 当日去重后 **{len(recent)}** 条 \\| 跨{DEDUP_DAYS}天过滤 **{cross_day_dropped}** 条\n",
    "> 评分：营销洞察/案例(0-3) + 媒介投放(0-2) + 电商运营(0-2) + AI营销(0-2) + 内容质量(0-1)\n",
    "> 注：微信 RSS 不暴露阅读量等指标；若有数据均为文章正文中显式提及\n",
    "\n---\n",
]

MIN_SCORE = 4  # 低于此分的文章不进入精选
AD_KEYWORDS = ['金冠俱乐部', '独角招聘', '热招中', '晋升通道', '员工福利', '招聘岗位']  # 明显广告帖直接过滤
MAX_TOTAL = 40  # 精选总条数上限（不含平台官方账号）

# 平台官方账号（京东/字节/小红书/腾讯/百度）不受 MIN_SCORE 限制，单独追加，不占 MAX_TOTAL 名额
all_qualified = []
platform_items = []
for cat in CAT_ORDER:
    if cat not in by_cat or not by_cat[cat]:
        continue
    for it in by_cat[cat]:
        if it.get('source') in SOURCE_PLATFORM_MAP:
            # 平台官方账号 → 无条件保留，但去广告帖
            if not any(k in (it['title'] or '') for k in AD_KEYWORDS):
                platform_items.append((it, cat))
        elif it['score'] >= MIN_SCORE and not any(k in (it['title'] or '') for k in AD_KEYWORDS):
            all_qualified.append((it, cat))

# 非平台文章：按分数降序，截断至 MAX_TOTAL
all_qualified.sort(key=lambda x: x[0]['score'], reverse=True)
capped = all_qualified[:MAX_TOTAL]

# 平台官方账号文章：全部追加在后面（不受 MAX_TOTAL 限制）
platform_items.sort(key=lambda x: x[0]['score'], reverse=True)
capped.extend(platform_items)

# 按 CAT_ORDER 分组输出
for cat in CAT_ORDER:
    items = [it for it, c in capped if c == cat]
    if not items:
        continue
    emoji = CAT_EMOJI.get(cat, '📝')
    lines.append(f"\n## {emoji} {cat}（{len(items)}条）\n")
    for it in items:
        pub_str = it['pub'].strftime('%m-%d %H:%M') if it['pub'] else ''
        eng = it['engagement']
        eng_str = ''
        if eng:
            parts = [f"{k}：{v}" for k, v in eng.items()]
            eng_str = ' | ' + ' '.join(parts)
        lines.append(f"### [{it['title']}]({it['link']})")
        lines.append(f"\n来源：{it['source']} \\| {pub_str} \\| 评分：**{it['score']}/10**{eng_str}\n")
        sent = first_sentence(it['text'])
        if sent:
            lines.append(f"\n> {sent}\n")
        lines.append("\n---\n")

output = '\n'.join(lines)
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    f.write(output)

sent_history = history_items + [
    {
        'date': YD_STR,
        'title': it.get('title', ''),
        'link': it.get('link', ''),
        'fingerprint': title_fp(it.get('title', '')),
        'cat': it.get('cat', ''),
        'source': it.get('source', ''),
    }
    for it, _ in capped
]
save_dedup_history(sent_history)
save_checkpoint(stage='done', total_feeds=len(feeds), completed_feeds=len(feeds), stats=stats, item_count=len(capped))

size = os.path.getsize(OUTPUT_FILE)
qualified_total = len(capped)
print(f"\n完成！\n文件: {OUTPUT_FILE}\n大小: {size} bytes")
print(f"总条数: {len(recent)}条 | 精选(≥{MIN_SCORE}分): {qualified_total}条")

