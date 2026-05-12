#!/usr/bin/env python3
"""
RSS 精选脚本 v4
- 排他性分类（每篇文章只归一个分类，不重复）
- 带原文链接
- 提取正文中的互动指标（阅读量/在看/评论等显式数据）
- 只输出昨天内容
- 评分系统：0-10分，门槛≥4分，上限40条
"""
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
import re, html, os

OPML_FILE = os.path.expanduser('~/.openclaw/workspace-dev/data/wechat_rss_subscriptions.opml')
RSS_SERVER = 'http://s.ztso.xyz:11211/feed'
TIMEOUT = 12
CST = timezone(timedelta(hours=8))
YESTERDAY = datetime.now(CST) - timedelta(days=1)
YD_STR = YESTERDAY.strftime('%Y-%m-%d')
YD_SHORT = YESTERDAY.strftime('%m-%d')
OUTPUT_FILE = os.path.expanduser(f'~/.openclaw/workspace-dev/output/rss_daily_{YD_STR}.md')
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
ATOM_NS = 'http://www.w3.org/2005/Atom'
CONTENT_NS = 'http://purl.org/rss/1.0/modules/content/'

# 飞书配置
FEISHU_APP_ID = os.environ.get('FEISHU_APP_ID', '')
FEISHU_APP_SECRET = os.environ.get('FEISHU_APP_SECRET', '')
FEISHU_USER_OPENID = 'ou_d635f4f3d20ac474cf8575038b5d2b33'

CAT_EMOJI = {
    '京东': '🟣', '字节': '🔵', '小红书': '🔴', '腾讯': '🟢', '百度': '⚪',
    '营销+AI': '🤖', '电商零售': '🛒', '营销增长': '📈'
}
CAT_ORDER = ['京东', '字节', '小红书', '腾讯', '百度', '营销+AI', '电商零售', '营销增长']

# 来源账号 → 平台官方分类（优先级最高）
SOURCE_PLATFORM_MAP = {
    # 京东
    "京东黑板报": "京东",
    "京准通": "京东",
    "京麦商家中心": "京东",
    "京东研究院": "京东",
    # 字节/抖音
    "巨量引擎营销观察": "字节",
    "巨量引擎营销科学": "字节",
    "抖音电商营销观察": "字节",
    # 小红书
    "小红书种草学": "小红书",
    "小红书商业动态": "小红书",
    "小红书技术REDtech": "小红书",
    # 腾讯
    "腾讯广告": "腾讯",
    # 百度
    "百度营销观": "百度",
}

# 广告关键词黑名单
AD_KEYWORDS = ['金冠俱乐部', '独角招聘', '热招中', '晋升通道', '员工福利', '招聘岗位', '求职', '猎头', '诚聘', '免费领', '限时抢', '立即购买', '优惠码', '满减', '0元', '0元购', '转给朋友', '扩散', '建议收藏', '朋友圈']


def tag(local):
    return f'{{{ATOM_NS}}}{local}'


def parse_date(text):
    if not text:
        return None
    text = text.strip()
    try:
        dt = datetime.strptime(text[:25], '%a, %d %b %Y %H:%M:%S')
        return dt.replace(tzinfo=timezone.utc).astimezone(CST)
    except:
        try:
            dt = datetime.fromisoformat(text.replace('Z', '+00:00'))
            return dt.astimezone(CST)
        except:
            return None


def classify(title, content, source):
    """排他性分类：
    - 官方平台账号（SOURCE_PLATFORM_MAP） → 对应平台分类
    - 其他账号 → 按内容关键词分入 topic 分类
    """
    if source in SOURCE_PLATFORM_MAP:
        return SOURCE_PLATFORM_MAP[source]
    t = (title or '').lower()
    c = ((content or '')[:3000]).lower()
    # 营销+AI
    ai_kw = ['ai', '人工智能', 'gpt', '大模型', '自动化', 'aigc', '数字人',
             'deepseek', 'chatgpt', '智能投放', 'geo', 'ai营销', 'claude',
             'genai', 'llm', 'agent', '智能体', '工作流', 'gpt-4', 'o1', 'o3', 'gemini']
    if any(k in t or k in c for k in ai_kw):
        return '营销+AI'
    # 电商零售
    ec_kw = ['电商', '零售', '直播带货', '天猫', '淘宝', '选品', '跨境',
             '亚马逊', 'shopify', '私域', '拼多多', '唯品会', '即时零售',
             '货架电商', '跨境电商', '电商平台', '电商运营', '京东', 'jd.com']
    if any(k in t or k in c for k in ec_kw):
        return '电商零售'
    return '营销增长'


def score_article(title, content):
    """评分系统：0-10分（优化版 v2）
    加权维度：
      媒介竞价投放(0-4) + 电商投放内容(0-3) + 案例/模式(0-2) + AI营销(0-1)
    核心聚焦：竞价投放技巧、电商投放策略、实战案例、商业模式
    关键改进：用 (关键词, 权重) 元组 + 计数上限，避免小数累加不到门槛
    """
    t = (title or '').lower()
    c = ((content or '')[:3000]).lower()
    score = 0

    # ========== 1. 媒介竞价投放（核心加权）: 0-4分 ==========
    # 核心竞价关键词（高权重，最多计2个命中）
    bidding_core = [
        ('竞价', 2.0), ('出价', 1.8), ('出价策略', 2.0), ('智能出价', 1.8),
        ('cpm', 1.8), ('cpc', 1.8), ('ocpm', 1.8), ('ocpc', 1.8), ('ecpm', 1.8),
        ('千次展现', 1.5), ('点击成本', 1.5), ('转化成本', 1.5), ('获客成本', 1.5),
        ('投放消耗', 1.5), ('日耗', 1.5), ('消耗', 1.2),
        ('预算分配', 1.5), ('预算控制', 1.5), ('账户余额', 1.2), ('账户结构', 1.5),
    ]
    core_count = 0
    for kw, w in bidding_core:
        if core_count >= 2:
            break
        if kw in t:
            score += w
            core_count += 1
        elif kw in c:
            score += w * 0.5

    # 投放优化/效果关键词（中权重，最多计3个命中）
    bidding_opt = [
        ('投放优化', 1.2), ('降成本', 1.2), ('降低成本', 1.2),
        ('提roi', 1.2), ('提升roi', 1.2), ('roi提升', 1.2),
        ('ctr优化', 1.0), ('点击率优化', 1.0), ('转化率提升', 1.0),
        ('放量', 0.8), ('缩窄', 0.8),
        ('定向优化', 1.0), ('人群包', 0.8), ('dmp', 0.8), ('人群定向', 1.0), ('重定向', 0.8),
        ('ab测试', 0.8), ('a/b测试', 0.8), ('多账户', 0.8), ('计划结构', 0.8),
        ('投放复盘', 1.0), ('投放数据', 0.8), ('投放效果', 0.8), ('投放案例', 0.8),
    ]
    opt_count = 0
    for kw, w in bidding_opt:
        if opt_count >= 3:
            break
        if kw in t:
            score += w
            opt_count += 1
        elif kw in c:
            score += w * 0.5

    # 基础投放/平台工具词汇（低权重，可累加多个）
    bidding_base = [
        '信息流', '竞价广告', '效果广告', '搜索广告', '展示广告',
        '广告投放', '媒介投放', '投放策略', '投放技巧', '投流',
        '付费流量', '买量', '投手', '优化师', '投流团队',
        '千川', '巨量', '聚光', '京准通', '直通车', '万相台', '引力魔方',
        '抖音投放', '小红书投放', '腾讯广告', '淘宝投放', '京东投放',
    ]
    base_count = 0
    for kw in bidding_base:
        if base_count >= 3:
            break
        if kw in t:
            score += 0.5
            base_count += 1
        elif kw in c:
            score += 0.3

    score = min(4, score)  # 封顶4分

    # ========== 2. 电商投放内容（加权）: 0-3分 ==========
    ec_ads_core = [
        ('电商投放', 1.2), ('店铺推广', 1.0), ('商品推广', 1.0),
        ('直播间投流', 1.2), ('短视频投流', 1.2), ('带货投放', 1.2),
        ('roi', 1.0), ('gmv', 1.0), ('投产比', 1.0),
    ]
    ec_count = 0
    for kw, w in ec_ads_core:
        if ec_count >= 2:
            break
        if kw in t:
            score += w
            ec_count += 1
        elif kw in c:
            score += w * 0.5

    ec_base = ['直播带货', '种草', '收割', '私域', '复购', '客单价', '选品',
               '货架电商', '直播电商', '内容电商']
    for kw in ec_base:
        if kw in t:
            score += 0.5
        elif kw in c:
            score += 0.3

    score = min(3, score)  # 封顶3分

    # ========== 3. 案例与商业模式: 0-2分 ==========
    case_kw = [
        ('案例', 0.8), ('实战', 0.8), ('方法论', 0.8), ('操盘', 0.8),
        ('复盘', 0.8), ('拆解', 0.8), ('打法', 0.8),
        ('模式', 0.6), ('商业模式', 0.6), ('盈利模型', 0.6), ('变现', 0.6),
        ('冷启动', 0.8), ('起量', 0.8), ('爆量', 0.8), ('日销', 0.6),
        ('实操', 0.8), ('全链路', 0.6),
    ]
    case_count = 0
    for kw, w in case_kw:
        if case_count >= 2:
            break
        if kw in t:
            score += w
            case_count += 1
        elif kw in c:
            score += w * 0.4

    score = min(2, score)  # 封顶2分

    # ========== 4. AI营销（辅助）: 0-1分 ==========
    ai_kw = ['智能投放', '自动化投放', '智能出价', 'ai优化', '算法推荐',
             'aigc素材', '数字人直播', 'ai投手', '智能定向']
    if any(k in t or k in c for k in ai_kw):
        score += 0.5

    ai_general = ['ai', '人工智能', '大模型', 'chatgpt', 'deepseek', 'genai']
    if any(k in t for k in ai_general):
        score += 0.3

    score = min(1, score)  # 封顶1分

    # ========== 5. 内容质量: 0-1分 ==========
    content_len = len(content or '')
    if content_len > 2000 and '。' in c:
        score += 0.5
    if content_len > 3000 and ('案例' in c or '数据' in c or 'roi' in c):
        score += 0.5

    # ========== 6. 低质指标惩罚 ==========
    foreign = ['meta', 'facebook', '亚马逊', 'amazon', 'tiktok', 'youtube',
               'google', 'instagram', 'snapchat', 'twitter', 'linkedin']
    if any(k in t for k in foreign):
        score -= 2

    if any(k in t for k in ['马斯克', '特朗普', '普京', '拜登', '权谈']):
        score -= 1

    if title and len(title) < 12:
        score -= 0.5

    return max(0, round(score, 1))


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
    for ch in '【】[]（）()｜|:：,,。.!！？?"""''、、/-_':
        t = t.replace(ch, ' ')
    return ' '.join(t.split())


def title_fp(title):
    tokens = [tok for tok in normalize_text(title).split() if len(tok) > 1]
    return ' '.join(tokens[:12])


def get_session():
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    s = requests.Session()
    retry = Retry(total=2, connect=2, read=2, backoff_factor=0.8,
                  status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["GET", "POST"])
    adapter = HTTPAdapter(max_retries=retry, pool_connections=20, pool_maxsize=20)
    s.mount('http://', adapter)
    s.mount('https://', adapter)
    s.headers.update({'User-Agent': 'daily-news-sync/v4'})
    return s


def parse_feed(sid, feed_title):
    url = f'{RSS_SERVER}/{sid}.atom'
    try:
        r = get_session().get(url, timeout=TIMEOUT)
        r.encoding = 'utf-8'
        root = ET.fromstring(r.text)
        items = []
        for entry in root.findall('.//' + tag('entry')):
            title_el = entry.find(tag('title'))
            link_el = entry.find(tag('link'))
            updated_el = entry.find(tag('updated'))
            content_el = entry.find(f'{{{CONTENT_NS}}}encoded')
            title = html.unescape(title_el.text or '') if title_el is not None else ''
            link = (link_el.get('href') or '') if link_el is not None else ''
            pub = parse_date(updated_el.text if updated_el is not None else '')
            content = html.unescape(content_el.text) if content_el is not None and content_el.text else ''
            if not title or not link:
                continue
            items.append({'title': title, 'link': link, 'pub': pub, 'source': feed_title, 'content': content})
        return items
    except:
        return []


def load_sources_from_opml():
    """从OPML加载公众号来源"""
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
    except:
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
    # 阅读量
    m = re.search(r'阅读[量数：:]*\s*([\d十百千万余\.]+万\+?)', t)
    if m:
        result['阅读量'] = m.group(1)
    m = re.search(r'([\d\.]+万\+?)\+?\s*(?:阅读|浏览)', t)
    if m and '阅读量' not in result:
        result['阅读量'] = m.group(1)
    # 在看/点赞
    m = re.search(r'在看[：:]*\s*([\d十百千万余\.]+万\+?)', t)
    if m:
        result['在看'] = m.group(1)
    # 评论
    m = re.search(r'评论[数：:]*\s*([\d十百千万余\.]+万\+?)', t)
    if m:
        result['评论'] = m.group(1)
    m = re.search(r'([\d\.]+万\+?)\s*(?:评论|留言)', t)
    if m and '评论' not in result:
        result['评论'] = m.group(1)
    # 转发
    m = re.search(r'转发[量：:]*\s*([\d十百千万余\.]+万\+?)', t)
    if m:
        result['转发'] = m.group(1)
    return result


def first_sentence(text, max_len=120):
    """提取第一句有意义的正文"""
    if not text:
        return ''
    skip_prefixes = ['来源', '作者', '未经授权', '转载', 'copyright', '©', '相关阅读',
                     '点击', '关注', '扫描', '二维码', '免责声明', '广告', '推广']
    sentences = re.findall(r'[^。！？.!?]{20,150}[。！？.!?]', text)
    for s in sentences:
        if not any(s.lower().startswith(p.lower()) for p in skip_prefixes):
            return s[:max_len]
    return (text[:max_len] + '…') if len(text) > max_len else text


def get_feishu_token():
    url = 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal'
    resp = requests.post(url, json={'app_id': FEISHU_APP_ID, 'app_secret': FEISHU_APP_SECRET})
    if resp.status_code == 200:
        data = resp.json()
        if data.get('code') == 0:
            return data.get('tenant_access_token')
    return None


# === 主流程 ===
print(f"=== RSS 精选 v4 | {YD_STR} ===")

print("Step 1: 解析 OPML...")
sources = load_sources_from_opml()
print(f"  共 {len(sources)} 个 RSS 源")

print("Step 2: 并行抓取 feeds...")
all_items = []
seen_fp = set()

with ThreadPoolExecutor(max_workers=10) as ex:
    futures = {ex.submit(parse_feed, src['id'], src['name']): src for src in sources}
    for i, future in enumerate(as_completed(futures)):
        try:
            for item in future.result():
                fp = title_fp(item['title'])
                if fp and fp not in seen_fp and not is_noise(item['title']):
                    seen_fp.add(fp)
                    all_items.append(item)
        except:
            pass
        if (i+1) % 10 == 0:
            print(f"  {i+1}/{len(sources)}")

print(f"  去重后: {len(all_items)} 条")

# 只保留昨天
yd_start = datetime(YESTERDAY.year, YESTERDAY.month, YESTERDAY.day, 0, 0, 0, tzinfo=CST)
yd_end = datetime(YESTERDAY.year, YESTERDAY.month, YESTERDAY.day, 23, 59, 59, tzinfo=CST)
recent = [it for it in all_items if it['pub'] and yd_start <= it['pub'] <= yd_end]
print(f"  昨天 {YD_SHORT}: {len(recent)} 条")

# 排他性分类 + 打分 + 正文提取 + 互动指标
seen_links = set()
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

# 按分类分组，分类内按分数降序
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
MIN_SCORE = 4
MAX_TOTAL = 40

all_qualified = []
for cat in CAT_ORDER:
    if cat not in by_cat or not by_cat[cat]:
        continue
    qualified = [
        it for it in by_cat[cat]
        if it['score'] >= MIN_SCORE
        and not any(k in (it['title'] or '') for k in AD_KEYWORDS)
    ]
    all_qualified.extend([(it, cat) for it in qualified])

all_qualified.sort(key=lambda x: x[0]['score'], reverse=True)
capped = all_qualified[:MAX_TOTAL]

lines = [
    f'# 每日资讯精选 | {YD_STR}（昨日）\n',
    f"\n> 共抓取 **{len(all_items)}** 条 | 昨日去重 **{len(recent)}** 条 | 精选(≥{MIN_SCORE}分) **{len(capped)}** 条\n",
    "> 评分：营销洞察/案例(0-3) + 媒介投放(0-2) + 电商运营(0-2) + AI营销(0-2) + 内容质量(0-1)\n",
    "> 注：微信 RSS 不暴露阅读量等指标；若有数据均为文章正文中显式提及\n",
    "\n---\n",
]

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
        lines.append(f"\n来源：{it['source']} | {pub_str} | 评分：**{it['score']}/10**{eng_str}\n")
        sent = first_sentence(it['text'])
        if sent:
            lines.append(f"\n> {sent}\n")
        lines.append("\n---\n")

output = '\n'.join(lines)
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    f.write(output)

print(f"\n完成！")
print(f"文件: {OUTPUT_FILE}")
print(f"总条数: {len(recent)}条 | 精选(≥{MIN_SCORE}分): {len(capped)}条")

# 输出飞书内容标记
print("\n" + "="*60)
print("FEISHU_CONTENT_START")
print(output)
print("FEISHU_CONTENT_END")
print("="*60)
print(f"\nFEISHU_TITLE: 每日资讯精选 | {YD_STR}")
print(f"\n✅ 请使用 feishu_create_doc 工具创建飞书文档")
