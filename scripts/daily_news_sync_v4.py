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
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

RSS_SERVER = 'http://s.ztso.xyz:11211/feed'
OPML_FILE = os.path.expanduser('~/.openclaw/workspace-dev/data/wechat_rss_subscriptions.opml')
CHECKPOINT_FILE = os.path.expanduser('~/.openclaw/workspace-dev/data/daily_news_checkpoint.json')
DEDUP_HISTORY_FILE = os.path.expanduser('~/.openclaw/workspace-dev/data/daily_news_dedup_history.json')
DEDUP_DAYS = 7
OUTPUT_DIR = os.path.expanduser('~/.openclaw/workspace-dev/output')

# AI API 配置（12AI MiniMax）
AI_API_URL = 'https://cdn.12ai.org/v1/chat/completions'
AI_API_KEY = os.environ.get('TWELVEAI_API_KEY', 'sk-8xBdlzdEiSP3QDjKna7fDDMknJ4Bh6YLNUrxFruG7ZPGxszf')
AI_MODEL = 'minimax-cn/MiniMax-Text-01'

# Discord channel ID
DISCORD_CHANNEL_ID = '1478997781187268608'
# Discord bot token
DISCORD_BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN', '')

# 飞书配置
FEISHU_APP_ID = os.environ.get('FEISHU_APP_ID', '')
FEISHU_APP_SECRET = os.environ.get('FEISHU_APP_SECRET', '')
FEISHU_USER_OPENID = 'ou_d635f4f3d20ac474cf8575038b5d2b33'

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
    """识别广告软文 / 招聘内容，排除噪音"""
    t = (title or '')
    if any(k in t for k in ['【诚聘】', '【招聘】', '【急招】', '诚聘', '加入我们', '猎头', 'HR诚聘', '高薪诚聘',
                       '薪资面议', '跳槽', 'offer直达', 'offer', '面试', '入职', '简历投递']):
        return True
    if any(k in t for k in ['免费领', '限时抢', '立即购买', '优惠码', '满减', '0元购', '1元购',
                             '惊喜价', '优惠价', '全网首发', '限时优惠', '0门槛']):
        return True
    if any(k in t for k in ['转给朋友', '扩散', '建议收藏', '朋友圈', '求求了', '救命']):
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
    with open(CHECKPOINT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


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
                        'date': item['date']
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
    批量 AI 分类：一次 API 调用处理所有文章
    AI 理解意图后返回每个文章的分类 + 评分 + 是否推荐入选
    """
    if not articles:
        return {}

    # 构建 prompt
    article_list = []
    for i, art in enumerate(articles):
        article_list.append(f"[{i}] {art['title']} | 来源：{art['source']} | 关键词预分类：{art.get('cat', '其他')}")

    prompt = f"""你是一个专注于国内竞价媒体与电商的资讯分类助手。

## 任务
对以下文章进行分类和评分，返回 JSON 格式结果。

## 分类定义（严格按此分类，优先级：京东/抖音/阿里妈妈/小红书 > 电商零售 > 营销+AI > 营销增长 > 其他）
- 京东：京东站内投放、京东联盟、京东商家运营、京东广告产品（标题有"京东"→京东，不是营销+AI）
- 抖音：抖音/巨量引擎投放、抖音电商、巨量千川、字节系营销（标题有"抖音"或"字节"→抖音，不是营销+AI）
- 阿里妈妈：淘系广告（直通车、引力魔方、达摩盘、钻展等）、多多搜索、多多场景、淘宝客
- 小红书：小红书种草/聚光投放、小红书商家运营、小红书广告
- 电商零售：电商运营、直播带货、天猫淘宝拼多多、电商转化链路、品牌零售、消费品
- 营销+AI：AI辅助投放工具、大模型应用在营销场景（AIGC内容生成、AI广告素材、AI客服/私域、Agent自动化投放）。注意：平台动态报道（如"抖音上线AI功能"）、公司AI融资、AI硬件、电商零售文章即使提到AI也不算营销+AI
- 营销增长：竞价广告、信息流、投放策略、营销案例、行业报告（不在以上分类的泛商业内容）
- 其他：不属于以上分类的内容

## 营销+AI 严格判断标准（容易分错，重点看）
以下情况 → **不是** 营销+AI：
- 标题有"京东""抖音""字节""阿里妈妈""小红书" → 归对应平台分类，即使提到AI工具
- 电商零售文章（"枕头赛道""天猫运营""直播带货""品牌落子"）→ 电商零售
- 公司AI新闻/融资（"商汤医疗AI融资""跻身独角兽"）→ 不是营销+AI
- AI硬件/产品（"AI手机""AI眼镜"）→ 其他
- 标题提了"AI"但文章主要是营销增长内容 → 营销增长

以下情况 → **是** 营销+AI：
- AIGC批量生成广告素材/文案/视频的具体方法
- AI工具在投放中的实测对比/使用教程
- 大模型（如DeepSeek/Kimi/文心）如何提升竞价效率
- AI Agent自动化投放的具体案例

## 评分标准（0-10，营销+AI文章要特别严格）
- 营销洞察/案例(0-3)：有数据、有方法论、有复盘 → +1-3分
- 媒介投放价值(0-2)：涉及投放/广告/竞价策略 → +1-2分
- 电商运营价值(0-2)：涉及电商转化/选品/供应链 → +1-2分
- AI营销价值(0-2)：
  - 真正讲AI工具在投放中应用（含具体方法、数据、对比）→ +2分
  - 泛泛提到AI但无实操价值（如"AI时代来临"）→ +0-1分
  - 标题蹭AI热度但文章主题不是AI营销 → +0分
- 内容质量(0-1)：正文超过500字且有数据 → +1分
- 噪音惩罚：标题含马斯克/特朗普/无意义标题/纯新闻汇总 → -1分

## 重要提醒
- 每分类目标约4-14条，不要把文章都塞进营销+AI
- 平台分类（京东/抖音/阿里妈妈/小红书）优先于营销+AI
- 营销+AI宁少勿滥：没有具体AI营销方法的文章 → 营销增长

## 每分类目标数量
- 营销增长: 14条
- 电商零售: 12条
- 阿里妈妈: 5条
- 抖音: 4条
- 小红书: 4条
- 京东: 3条
- 营销+AI: 4条
- 其他: 4条
总计约 46 条

## 输出格式
返回 JSON 对象，key 是文章序号 [0] 到 [{len(articles)-1}]，value 是：
{{"cat": "分类名", "score": 0-10整数, "recommend": true/false, "reason": "简短理由"}}

## 注意
- recommend=true 表示值得入选精选
- 同一分类优先选分数高的
- 只返回 JSON，不要其他内容
- 严格使用上面定义的8个分类名

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
        resp = requests.post(AI_API_URL, headers=headers, json=payload, timeout=120)
        if resp.status_code != 200:
            print(f"[WARN] AI API error: {resp.status_code} - {resp.text[:200]}")
            return {}
        result_text = resp.json()['choices'][0]['message']['content'].strip()

        # 提取 JSON
        import re
        json_match = re.search(r'\{[\s\S]*\}', result_text)
        if json_match:
            result = json.loads(json_match.group())
            print(f"[AI] 成功分类 {len(result)} 篇文章")
            return result
        else:
            print(f"[WARN] AI 返回非JSON: {result_text[:200]}")
            return {}
    except Exception as e:
        print(f"[ERR] AI 分类失败: {type(e).__name__}: {e}")
        return {}


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
    url = 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal'
    resp = requests.post(url, json={'app_id': FEISHU_APP_ID, 'app_secret': FEISHU_APP_SECRET})
    if resp.status_code == 200:
        data = resp.json()
        if data.get('code') == 0:
            return data.get('tenant_access_token')
    return None


def send_feishu_im(token, content, receive_id_type='open_id', receive_id=None):
    """发送飞书 IM 消息给 Gary"""
    if not receive_id:
        receive_id = FEISHU_USER_OPENID
    url = 'https://open.feishu.cn/open-apis/im/v1/messages'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    # 飞书单条消息最大 6000 字符，按需分割
    MAX_LEN = 5800
    chunks = []
    for i in range(0, len(content), MAX_LEN):
        chunks.append(content[i:i+MAX_LEN])

    for idx, chunk in enumerate(chunks):
        payload = {
            'receive_id': receive_id,
            'receive_id_type': receive_id_type,
            'msg_type': 'text',
            'content': json.dumps({'text': chunk})
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=15)
            result = resp.json()
            if result.get('code') == 0:
                print(f"[Feishu IM] 发送成功 ({idx+1}/{len(chunks)}) ✅")
            else:
                print(f"[Feishu IM] 发送失败: {result.get('msg')} ({result.get('code')})")
        except Exception as e:
            print(f"[Feishu IM] 异常: {type(e).__name__}: {e}")


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

    def make_para(text):
        """创建一个段落 block"""
        return {
            'block_type': 2,  # paragraph
            'paragraph': {
                'elements': [{'text_run': {'content': text}}],
                'style': {}
            }
        }

    blocks = []
    # 标题
    blocks.append(make_para(f"📋 每日资讯精选 {yesterday} | 完整{len(articles)}条"))
    blocks.append({'block_type': 2, 'paragraph': {'elements': [{'text_run': {'content': ' '}}], 'style': {}}})

    for cat in CAT_ORDER:
        items = selected_cats.get(cat, [])
        if not items:
            continue
        emoji = CAT_EMOJI[cat]
        blocks.append(make_para(f"\n{emoji} {cat}（{len(items)}条）"))
        for item in items:
            blocks.append(make_para(item['title']))
            blocks.append(make_para(item['link']))

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
            f"近{DEDUP_DAYS}天重复内容已自动过滤：{len(dedup_dropped)}条。\n"
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


def build_feishu_im_content(articles, yesterday, selected_cats, doc_url=None):
    """构建飞书 IM 消息内容（2行/条格式：标题+链接，全部40条，一口气发出）"""
    if not articles:
        return None

    lines = [
        f"📋 每日资讯精选 {yesterday} | 完整{len(articles)}条\n"
    ]

    for cat in CAT_ORDER:
        items = selected_cats.get(cat, [])
        if not items:
            continue
        emoji = CAT_EMOJI[cat]
        lines.append(f"\n{emoji} {cat}（{len(items)}条）")
        for item in items:
            lines.append(item['title'])
            lines.append(item['link'])

    if doc_url:
        lines.append(f"\n📄 完整版（{len(articles)}条全文）：{doc_url}")

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

    # 创建飞书文档存档（脚本直接调用 API）
    print("\n[Feishu Doc] 创建飞书文档存档...")
    token = get_feishu_token()
    doc_url = None
    if token:
        doc_url = create_feishu_doc(token, doc_title, selected_items, yesterday, selected_cats)
    else:
        print("[Feishu Doc] 获取 token 失败，跳过文档创建")

    # Discord 摘要
    discord_content = build_discord_content(selected_items, yesterday, selected_cats)
    if discord_content:
        print("\n[Discord] 发送摘要...")
        if send_discord(discord_content):
            print("[Discord] 发送成功 ✅")
        else:
            print("[Discord] 发送失败")

    # 飞书 IM 消息（全部40条，一条消息发出）
    feishu_im_content = build_feishu_im_content(selected_items, yesterday, selected_cats, doc_url=doc_url)
    if feishu_im_content:
        print("\n[Feishu IM] 发送资讯到 Gary DM...")
        token = get_feishu_token()
        if token:
            send_feishu_im(token, feishu_im_content)
        else:
            print("[Feishu IM] 获取 token 失败，跳过")

    # 保存去重历史
    save_dedup_history(new_history)

    # 保存 checkpoint
    output_file = os.path.join(OUTPUT_DIR, f'rss_daily_{yesterday}_selected.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'date': yesterday,
            'total_raw': raw_count,
            'total_selected': len(selected_items),
            'articles': selected_items
        }, f, ensure_ascii=False, indent=2)
    print(f"\n已保存: {output_file}")

    print(f"\n✅ 脚本执行完成")


if __name__ == '__main__':
    main()
