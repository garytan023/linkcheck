
# ============== 注意事项 ==============
# 京东反爬较严，建议使用以下方案：
# 1. Browser Relay（已登录态）- 效果最好
# 2. 代理池 + 延迟请求
# 3. 官方 API（淘宝开放平台 / 京东联盟）
#
# 当前实现使用 headless 浏览器，可能被检测拦截
# 建议在 OpenClaw 中使用 browser tool 配合已登录态爬取

#!/usr/bin/env python3
"""
京东商品体检工具 v2.0
核心逻辑：爬虫 + 12维度双评分（Human + AI）+ 对比分析 + 飞书报告生成
"""

import re
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse, parse_qs

# ============== 配置 ==============
MOBILE_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.0"
PC_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def extract_product_id(url: str) -> Optional[str]:
    """从京东链接提取商品ID"""
    patterns = [
        r"/(\d+)\.html",
        r"/product/(\d+)",
        r"/(\d{10,13})",
        r"sku=(\d+)",
        r"id=(\d+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def get_mobile_url(url: str) -> str:
    """转换为移动端商品页 URL"""
    product_id = extract_product_id(url)
    if product_id:
        return f"https://item.m.jd.com/product/{product_id}.html"
    return url


def get_pc_url(url: str) -> str:
    """转换为PC端商品页 URL"""
    product_id = extract_product_id(url)
    if product_id:
        return f"https://item.jd.com/{product_id}.html"
    return url


# ============== 12维度双评分体系 ==============
async def analyze_product(page, use_pc: bool = False) -> Dict:
    """
    爬取并分析京东商品页
    返回 12维度双评分结果（Human + AI）
    """
    # 提取商品数据
    product_data = await extract_product_data(page, use_pc)
    
    # 双维度 LLM 分析
    human_scores, ai_scores = await llm_analyze_dual(product_data)
    
    # 计算总分
    human_total = sum(human_scores.values()) // len(human_scores)
    ai_total = sum(ai_scores.values()) // len(ai_scores)
    
    # 生成修复建议
    fixes = generate_fixes_dual(human_scores, ai_scores)
    
    return {
        "product": product_data,
        "human_scores": human_scores,
        "ai_scores": ai_scores,
        "human_total": human_total,
        "ai_total": ai_total,
        "fixes": fixes
    }


async def extract_product_data(page, use_pc: bool = False) -> Dict:
    """从页面提取商品数据（优化版）"""
    data = {}
    
    # 标题
    try:
        title = await page.title()
        data["title"] = title
        if "【" in title:
            data["name"] = title.split("【")[0].strip()
        elif "-" in title:
            data["name"] = title.split("-")[0].strip()
        else:
            data["name"] = title
    except:
        data["name"] = "未知商品"
    
    # 主图（多种方式尝试）
    try:
        main_images = await page.evaluate(r"""() => {
            const images = [];
            const seen = new Set();
            
            // 方法1: #spec-list 下面的图片
            document.querySelectorAll("#spec-list img, .spec-items img").forEach(img => {
                if (img.src && !img.src.includes("blank") && !img.src.includes("1px")) {
                    const src = img.src.replace(/!\w+\./, "!pcsw.");
                    if (!seen.has(src)) { seen.add(src); images.push(src); }
                }
            });
            
            // 方法2: #main-img
            if (images.length < 3) {
                const mainImg = document.getElementById("main-img");
                if (mainImg && mainImg.src) {
                    images.push(mainImg.src.replace(/!\w+\./, "!pcsw."));
                }
            }
            
            // 方法3: 缩略图列表
            if (images.length < 3) {
                document.querySelectorAll(".spec-items li img, #spec-list li img").forEach(img => {
                    if (img.src && !seen.has(img.src)) {
                        seen.add(img.src);
                        images.push(img.src.replace(/!\w+\./, "!pcsw."));
                    }
                });
            }
            
            return images.slice(0, 10);
        }""")
        data["main_images"] = main_images
    except Exception as e:
        print(f"提取主图失败: {e}")
        data["main_images"] = []
    
    # 主图视频
    try:
        video_info = await page.evaluate("""() => {
            // 查找视频元素
            const video = document.querySelector("video");
            if (video && video.src) {
                return { has_video: true, duration: video.duration || 30 };
            }
            
            // 查找视频封面/按钮
            const videoBtn = document.querySelector('[class*="video"], .video-wrap, .play-icon, .video-icon');
            if (videoBtn) {
                return { has_video: true, duration: 30 };
            }
            
            // 从页面文本判断
            const text = document.body.innerText;
            if (text.includes("视频") && text.includes("主图")) {
                return { has_video: true, duration: 30 };
            }
            
            return { has_video: false, duration: 0 };
        }""")
        data["has_video"] = video_info.get("has_video", False)
        data["video_duration"] = video_info.get("duration", 0)
    except:
        data["has_video"] = False
        data["video_duration"] = 0
    
    # SKU - 从页面文本提取更可靠
    try:
        sku_data = await page.evaluate("""() => {
            const text = document.body.innerText;
            const skus = [];
            
            // 匹配颜色选项
            const colorMatch = text.match(/颜色[：:]([^\n]{5,50})/g);
            if (colorMatch) {
                colorMatch.forEach(m => {
                    const val = m.replace(/颜色[：:]/, "").trim();
                    if (val && val.length < 30) skus.push(val);
                });
            }
            
            // 匹配尺码
            const sizeMatch = text.match(/尺码[：:]([^\n]{5,30})/g);
            if (sizeMatch) {
                sizeMatch.forEach(m => {
                    const val = m.replace(/尺码[：:]/, "").trim();
                    if (val && val.length < 20) skus.push(val);
                });
            }
            
            // 匹配规格
            const specMatch = text.match(/规格[：:]([^\n]{5,20})/g);
            if (specMatch) {
                specMatch.forEach(m => {
                    const val = m.replace(/规格[：:]/, "").trim();
                    if (val && val.length < 15) skus.push(val);
                });
            }
            
            return [...new Set(skus)].slice(0, 30);
        }""")
        data["skus"] = sku_data
    except:
        data["skus"] = []
    
    # 店铺 - 多重尝试
    try:
        shop = await page.evaluate("""() => {
            // 从页面文本提取
            const text = document.body.innerText;
            const shopMatch = text.match(/(.+?京东自营店|.+\.com|旗舰店|专营店|官方旗舰店)/);
            if (shopMatch) return shopMatch[1].trim();
            
            // 从 DOM 提取
            const selectors = [
                ".shop-name a", 
                ".shop-info .name",
                "#shop-name .name",
                "[class*='shop'] [class*='name']",
                ".seller-info a"
            ];
            for (const sel of selectors) {
                const el = document.querySelector(sel);
                if (el && el.textContent.trim()) {
                    return el.textContent.trim();
                }
            }
            return null;
        }""")
        data["shop"] = shop or "未知店铺"
    except:
        data["shop"] = "未知店铺"
    
    # DSR 评分 - 从页面文本
    try:
        dsr = await page.evaluate("""() => {
            const text = document.body.innerText;
            const scores = { description: 0, service: 0, logistics: 0 };
            
            // 尝试匹配 "4.8" 这样的评分
            const matches = text.match(/(\d\.\d)\s*(分)?/g);
            if (matches) {
                const validScores = matches
                    .map(m => parseFloat(m))
                    .filter(s => s >= 4.0 && s <= 5.0)
                    .slice(0, 3);
                if (validScores.length > 0) scores.description = validScores[0];
                if (validScores.length > 1) scores.service = validScores[1];
                if (validScores.length > 2) scores.logistics = validScores[2];
            }
            
            // 如果还是 0，尝试从 DOM 获取
            if (scores.description === 0) {
                document.querySelectorAll("[class*='score'], .shop-score span").forEach(el => {
                    const score = parseFloat(el.textContent);
                    if (!isNaN(score) && score >= 4 && score <= 5) {
                        if (scores.description === 0) scores.description = score;
                        else if (scores.service === 0) scores.service = score;
                        else if (scores.logistics === 0) scores.logistics = score;
                    }
                });
            }
            
            return scores;
        }""")
        data["dsr"] = dsr
    except:
        data["dsr"] = {"description": 0, "service": 0, "logistics": 0}
    
    # 好评率
    try:
        good_rate = await page.evaluate("""() => {
            const text = document.body.innerText;
            
            // 多种匹配模式
            const patterns = [
                /好评率[：:]?\s*(\d+(\.\d+)?)%/,
                /(\d+(\.\d+)?)%\s*好评/,
                /超(\d+(\.\d+)?)%?好评/,
                /好评(?:率)?\s*[：:]?\s*(\d+)/,
                /(\d+(\.\d+)?)\s*%\s*(?:好|评)/
            ];
            
            for (const p of patterns) {
                const match = text.match(p);
                if (match) return parseFloat(match[1]);
            }
            return null;
        }""")
        data["good_rate"] = good_rate or 0
    except:
        data["good_rate"] = 0
    
    # 评价数量
    try:
        review_count = await page.evaluate("""() => {
            const text = document.body.innerText;
            
            // 匹配 "5万+条评价" 或 "50000+条评价"
            const patterns = [
                /(\d+(?:\.\d+)?万?)\+?\s*条?[评價评价]/,
                /评价[：:]\s*(\d+(?:\.\d+)?万?)/,
                /(\d+)\+?\s*(?:条)?评价/
            ];
            
            for (const p of patterns) {
                const match = text.match(p);
                if (match) {
                    let num = match[1];
                    if (num.includes("万")) return parseFloat(num) * 10000;
                    return parseInt(num);
                }
            }
            return 0;
        }""")
        data["review_count"] = review_count or 0
    except:
        data["review_count"] = 0
    
    # 库存状态
    try:
        stock_status = await page.evaluate("""() => {
            const text = document.body.innerText;
            const btnText = document.querySelector("#btn-buy, .btn-buy, .addcart, #InitCartUrl")?.textContent || "";
            const allText = text + btnText;
            
            if (allText.includes("无货") || allText.includes("缺货") || allText.includes("已售罄")) return "无货";
            if (allText.includes("预售") || allText.includes("预购")) return "预售";
            if (allText.includes("立即购买") || allText.includes("加入购物车") || allText.includes("有货")) return "有货";
            return "未知";
        }""")
        data["stock"] = stock_status or "未知"
    except:
        data["stock"] = "未知"
    
    # 价格
    try:
        price = await page.evaluate("""() => {
            const text = document.body.innerText;
            
            // 匹配价格
            const patterns = [
                /￥\s*(\d+(?:\.\d+)?)/,
                /RMB\s*(\d+(?:\.\d+)?)/,
                /价格[：:]\s*￥?\s*(\d+(?:\.\d+)?)/,
                /(\d+(?:\.\d+)?)\s*元/
            ];
            
            for (const p of patterns) {
                const match = text.match(p);
                if (match) return parseFloat(match[1]);
            }
            return 0;
        }""")
        data["price"] = price or 0
    except:
        data["price"] = 0
    
    # 问大家
    try:
        qa_count = await page.evaluate("""() => {
            const text = document.body.innerText;
            
            // 匹配问答数量
            const match = text.match(/(\d+)\s*个?问答/);
            if (match) return parseInt(match[1]);
            
            if (text.includes("暂无问答") || text.includes("没有问答")) return 0;
            return 0;
        }""")
        data["qa_count"] = qa_count or 0
    except:
        data["qa_count"] = 0
    
    return data
async def llm_analyze_dual(product_data: Dict) -> Tuple[Dict, Dict]:
    """
    使用 LLM 进行双维度评分
    返回: (Human评分, AI评分)
    """
    # 构建 prompt
    prompt = f"""你是一个专业的京东商品运营专家。请根据以下商品数据，给出12维度双评分。

商品信息：
- 商品名：{product_data.get('name', '未知')}
- 店铺：{product_data.get('shop', '未知')}
- 主图数量：{len(product_data.get('main_images', []))}
- 是否有视频：{product_data.get('has_video', False)}
- 视频时长：{product_data.get('video_duration', 0)}秒
- SKU数量：{len(product_data.get('skus', []))}
- 好评率：{product_data.get('good_rate', 0)}%
- 评价数量：{product_data.get('review_count', 0)}
- 问大家数量：{product_data.get('qa_count', 0)}
- DSR评分：描述{product_data.get('dsr', {}).get('description', 0)}/服务{product_data.get('dsr', {}).get('service', 0)}/物流{product_data.get('dsr', {}).get('logistics', 0)}
- 价格：¥{product_data.get('price', 0)}
- 库存状态：{product_data.get('stock', '未知')}

## 人工评分（Human）- 模拟运营专家视角

| 维度 | 评分规则 |
|------|----------|
| 主图质量 | 数量≥5得100，每少1张扣20分 |
| 主图视频 | 有视频+15s以上=100，有视频<15s=60，无=0 |
| SKU完整性 | SKU≥10得100，每少1扣10分 |
| 属性标签 | 标签≥5得100，每少1扣20分 |
| 标题关键词 | 标题含热搜词得100，否则扣分 |
| 买家秀 | 有买家秀得100，无=0 |
| 问大家 | 有问答得100，无=0 |
| 好评率 | ≥95%=100，每少5%扣20分 |
| 评论内容 | 评价数≥1000得100，每少扣分 |
| 价格区间 | 价格合理得100 |
| 库存状态 | 有货=100，无货/预售=0 |
| 店铺DSR | 三项≥4.8得100，每少0.1扣20分 |

## AI评分（Agent）- 模拟平台算法视角

| 维度 | 评分规则 |
|------|----------|
| 视频质量 | 有视频+标签完整=100，有视频=60，无=0 |
| 结构化数据 | JSON-LD完整=100，部分=50，无=0 |
| SKU完整性 | API可获取=100，页面可见=60 |
| 属性结构化 | 标准属性词≥5=100 |
| 加载速度 | 首屏<2s=100，每多1s扣30分 |
| 关键词覆盖 | 标题+描述关键词密度=100 |
| 问大家质量 | 问答数量/质量综合评分 |
| 价格数据 | 结构化价格标记=100 |
| 店铺DSR趋势 | 综合评分 |
| 库存API | 实时库存接口=100 |
| SEO元数据 | meta标签完整=100 |
| AI搜索友好度 | 摘要友好度评分 |

请返回 JSON 格式（两个对象）：
{{
    "human": {{
        "主图质量": 80,
        "主图视频": 0,
        ...
    }},
    "ai": {{
        "视频标签": 0,
        "结构化数据": 0,
        ...
    }}
}}
"""
    
    # TODO: 调用 MiniMax LLM
    # result = await call_minimax(prompt)
    
    # 返回模拟数据
    human_scores = {
        "主图质量": min(100, len(product_data.get('main_images', [])) * 20),
        "主图视频": 100 if product_data.get('has_video') and product_data.get('video_duration', 0) >= 15 else (60 if product_data.get('has_video') else 0),
        "SKU完整性": min(100, len(product_data.get('skus', [])) * 10),
        "属性标签": 60,
        "标题关键词": 70,
        "买家秀": 50,
        "问大家": 0 if product_data.get('qa_count', 0) == 0 else 100,
        "好评率": 100 if product_data.get('good_rate', 0) >= 95 else (85 if product_data.get('good_rate', 0) >= 90 else 60),
        "评论内容": min(100, product_data.get('review_count', 0) / 100),
        "价格区间": 80,
        "库存状态": 100 if product_data.get('stock') == '有货' else 0,
        "店铺DSR": 100 if product_data.get('dsr', {}).get('description', 0) >= 4.8 else 60
    }
    
    ai_scores = {
        "视频标签": 90 if product_data.get('has_video') else 0,
        "结构化数据": 70,
        "SKU完整性": 80 if len(product_data.get('skus', [])) > 0 else 0,
        "属性结构化": 60,
        "加载速度": 70,
        "关键词覆盖": 75,
        "问大家质量": 0 if product_data.get('qa_count', 0) == 0 else 70,
        "价格数据结构": 80,
        "店铺DSR": 100 if product_data.get('dsr', {}).get('description', 0) >= 4.8 else 60,
        "库存API": 50,
        "SEO元数据": 60,
        "AI搜索友好度": 75
    }
    
    return human_scores, ai_scores


def generate_fixes_dual(human_scores: Dict, ai_scores: Dict) -> List[Dict]:
    """生成双维度修复建议"""
    fixes = []
    
    priority_rules = {
        "human": {
            "主图视频": "添加主图视频（15s以上）",
            "买家秀": "上传优质买家秀",
            "问大家": "优化问大家内容",
            "好评率": "提升好评率到95%+",
            "评论内容": "增加评价数量和质量",
            "SKU完整性": "增加SKU变体"
        },
        "ai": {
            "视频标签": "完善视频标签和描述",
            "结构化数据": "添加JSON-LD结构化数据",
            "加载速度": "优化页面加载速度",
            "SEO元数据": "完善meta标签"
        }
    }
    
    # Human 维度
    for dimension, score in human_scores.items():
        if score < 60:
            fix_text = priority_rules["human"].get(dimension, f"优化{dimension}")
            fixes.append({
                "type": "human",
                "dimension": dimension,
                "score": score,
                "suggestion": f"🔴 {fix_text}（{score}分）"
            })
        elif score < 80:
            fix_text = priority_rules["human"].get(dimension, f"优化{dimension}")
            fixes.append({
                "type": "human",
                "dimension": dimension,
                "score": score,
                "suggestion": f"🟡 {fix_text}（{score}分）"
            })
    
    # AI 维度
    for dimension, score in ai_scores.items():
        if score < 60:
            fix_text = priority_rules["ai"].get(dimension, f"优化{dimension}")
            fixes.append({
                "type": "ai",
                "dimension": dimension,
                "score": score,
                "suggestion": f"🤖 {fix_text}（{score}分）"
            })
    
    return fixes


# ============== 对比功能 ==============
async def compare_products(url1: str, url2: str) -> str:
    """对比两个京东商品"""
    from playwright.async_api import async_playwright
    
    pc_url1 = get_pc_url(url1)
    pc_url2 = get_pc_url(url2)
    
    product_id1 = extract_product_id(pc_url1)
    product_id2 = extract_product_id(pc_url2)
    
    if not product_id1 or not product_id2:
        return "❌ 无法识别京东商品链接"
    
    print(f"对比商品: {product_id1} vs {product_id2}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        # 商品1
        context1 = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent=PC_UA,
            locale='zh-CN'
        )
        page1 = await context1.new_page()
        
        try:
            await page1.goto(pc_url1, wait_until="networkidle", timeout=30000)
            await page1.wait_for_timeout(2000)
            
            # 滚动触发懒加载
            await page1.evaluate("() => window.scrollTo(0, 500)")
            await page1.wait_for_timeout(1000)
            
            data1 = await extract_product_data(page1, use_pc=True)
            human1, ai1 = await llm_analyze_dual(data1)
        except Exception as e:
            print(f"商品1爬取失败: {e}")
            data1 = {"name": "商品1", "shop": "未知", "price": 0, "main_images": [], "has_video": False, "video_duration": 0, "skus": [], "good_rate": 0, "review_count": 0, "qa_count": 0, "dsr": {"description": 0, "service": 0, "logistics": 0}, "stock": "未知"}
            human1, ai1 = await llm_analyze_dual(data1)
        finally:
            await context1.close()
        
        # 商品2
        context2 = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent=PC_UA,
            locale='zh-CN'
        )
        page2 = await context2.new_page()
        
        try:
            await page2.goto(pc_url2, wait_until="networkidle", timeout=30000)
            await page2.wait_for_timeout(2000)
            
            await page2.evaluate("() => window.scrollTo(0, 500)")
            await page2.wait_for_timeout(1000)
            
            data2 = await extract_product_data(page2, use_pc=True)
            human2, ai2 = await llm_analyze_dual(data2)
        except Exception as e:
            print(f"商品2爬取失败: {e}")
            data2 = {"name": "商品2", "shop": "未知", "price": 0, "main_images": [], "has_video": False, "video_duration": 0, "skus": [], "good_rate": 0, "review_count": 0, "qa_count": 0, "dsr": {"description": 0, "service": 0, "logistics": 0}, "stock": "未知"}
            human2, ai2 = await llm_analyze_dual(data2)
        finally:
            await context2.close()
        
        await browser.close()
    
    # 生成对比报告
    report = generate_comparison_report(data1, human1, ai1, data2, human2, ai2, url1, url2)
    
    return report


def generate_comparison_report(
    data1: Dict, human1: Dict, ai1: Dict,
    data2: Dict, human2: Dict, ai2: Dict,
    url1: str, url2: str
) -> str:
    """生成对比报告"""
    
    product_id1 = extract_product_id(url1) or "未知"
    product_id2 = extract_product_id(url2) or "未知"
    
    # 获取商品名（简化）
    name1 = data1.get('name', '商品1')[:30]
    name2 = data2.get('name', '商品2')[:30]
    
    human_total1 = sum(human1.values()) // len(human1)
    human_total2 = sum(human2.values()) // len(human2)
    ai_total1 = sum(ai1.values()) // len(ai1)
    ai_total2 = sum(ai2.values()) // len(ai2)
    
    # 基础数据对比表
    comparison_md = f"""# 🔍 京东商品对比报告

## 基础数据对比

| 维度 | {name1[:15]} | {name2[:15]} |
|------|--------------|--------------|
| **商品ID** | {product_id1} | {product_id2} |
| **店铺** | {data1.get('shop', '未知')[:15]} | {data2.get('shop', '未知')[:15]} |
| **价格** | ¥{data1.get('price', 0)} | ¥{data2.get('price', 0)} |
| **主图数量** | {len(data1.get('main_images', []))}张 | {len(data2.get('main_images', []))}张 |
| **主图视频** | {'✅ ' + str(int(data1.get('video_duration', 0))) + '秒' if data1.get('has_video') else '❌'} | {'✅ ' + str(int(data2.get('video_duration', 0))) + '秒' if data2.get('has_video') else '❌'} |
| **评价数** | {int(data1.get('review_count', 0))}条 | {int(data2.get('review_count', 0))}条 |
| **好评率** | {data1.get('good_rate', 0)}% | {data2.get('good_rate', 0)}% |
| **SKU** | {len(data1.get('skus', []))}个 | {len(data2.get('skus', []))}个 |
| **店铺DSR** | {data1.get('dsr', {}).get('description', 0)}/{data1.get('dsr', {}).get('service', 0)}/{data1.get('dsr', {}).get('logistics', 0)} | {data2.get('dsr', {}).get('description', 0)}/{data2.get('dsr', {}).get('service', 0)}/{data2.get('dsr', {}).get('logistics', 0)} |
| **问大家** | {data1.get('qa_count', 0)}个 | {data2.get('qa_count', 0)}个 |

---

## 双维度评分对比

### 🎯 人工评分（Human）

| 维度 | {name1[:10]} | {name2[:10]} |
|------|-------------|-------------|
"""
    
    # Human 评分对比
    common_human_dims = set(human1.keys()) & set(human2.keys())
    for dim in sorted(common_human_dims):
        comparison_md += f"| {dim} | {human1[dim]} | {human2[dim]} |\n"
    
    comparison_md += f"| **总分** | **{human_total1}/100** | **{human_total2}/100** |\n\n"
    
    # AI 评分对比
    comparison_md += """### 🤖 AI 评分（Agent）

| 维度 | 商品1 | 商品2 |
|------|-------|-------|
"""
    
    common_ai_dims = set(ai1.keys()) & set(ai2.keys())
    for dim in sorted(common_ai_dims):
        comparison_md += f"| {dim} | {ai1[dim]} | {ai2[dim]} |\n"
    
    comparison_md += f"| **总分** | **{ai_total1}/100** | **{ai_total2}/100** |\n\n"
    
    # 结论
    comparison_md += """---

## 结论

| 视角 | 胜出 | 原因 |
|------|------|------|
"""
    
    if human_total1 > human_total2:
        human_winner = name1
        human_reason = f"人工评分更高（{human_total1} vs {human_total2}）"
    elif human_total2 > human_total1:
        human_winner = name2
        human_reason = f"人工评分更高（{human_total2} vs {human_total1}）"
    else:
        human_winner = "持平"
        human_reason = "人工评分相同"
    
    if ai_total1 > ai_total2:
        ai_winner = name1
        ai_reason = f"AI评分更高（{ai_total1} vs {ai_total2}）"
    elif ai_total2 > ai_total1:
        ai_winner = name2
        ai_reason = f"AI评分更高（{ai_total2} vs {ai_total1}）"
    else:
        ai_winner = "持平"
        ai_reason = "AI评分相同"
    
    comparison_md += f"| **Human** | {human_winner[:15]} | {human_reason} |\n"
    comparison_md += f"| **AI** | {ai_winner[:15]} | {ai_reason} |\n"
    
    comparison_md += f"""
---

> 对比时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
> 由 拉小码 AI 生成
"""
    
    return comparison_md



# ============== 飞书报告生成 ==============
async def generate_feishu_report(product_data: Dict, human_scores: Dict, ai_scores: Dict, fixes: List[Dict], product_url: str) -> str:
    """生成飞书云文档（单个商品）"""
    human_total = sum(human_scores.values()) // len(human_scores)
    ai_total = sum(ai_scores.values()) // len(ai_scores)
    total = (human_total + ai_total) // 2
    
    # 评分等级
    if total >= 90:
        grade = "🟢 优秀"
    elif total >= 75:
        grade = "🟡 良好"
    elif total >= 60:
        grade = "🟠 及格"
    else:
        grade = "🔴 需改进"
    
    product_id = extract_product_id(product_url) or "未知"
    
    report_md = f"""# 京东商品体检报告

## 商品信息

- **商品ID**: {product_id}
- **商品链接**: [查看商品]({product_url})
- **店铺**: {product_data.get('shop', '未知')}
- **主图数量**: {len(product_data.get('main_images', []))}
- **好评率**: {product_data.get('good_rate', 0)}%
- **评价数**: {int(product_data.get('review_count', 0))}条
- **价格**: ¥{product_data.get('price', 0)}

---

## 体检总分

**{total}/100** - {grade}

- Human评分: {human_total}/100
- AI评分: {ai_total}/100

---

## 🎯 人工评分（Human）

| 维度 | 分数 | 状态 |
|------|------|------|
"""
    
    for dim, score in human_scores.items():
        status = "🟢 优秀" if score >= 80 else ("🟡 良好" if score >= 60 else "🔴 需改进")
        report_md += f"| {dim} | {score} | {status} |\n"
    
    report_md += "\n## 🤖 AI 评分（Agent）\n\n| 维度 | 分数 | 状态 |\n|------|------|------|\n"
    
    for dim, score in ai_scores.items():
        status = "🟢 优秀" if score >= 80 else ("🟡 良好" if score >= 60 else "🔴 需改进")
        report_md += f"| {dim} | {score} | {status} |\n"
    
    # 修复建议
    human_fixes = [f for f in fixes if f["type"] == "human"]
    ai_fixes = [f for f in fixes if f["type"] == "ai"]
    
    report_md += "\n## 修复建议\n\n"
    
    if human_fixes:
        report_md += "### 🔴 高优先级（人工视角）\n\n"
        for f in human_fixes[:5]:
            report_md += f"- {f['suggestion']}\n"
    
    if ai_fixes:
        report_md += "\n### 🤖 高优先级（AI视角）\n\n"
        for f in ai_fixes[:5]:
            report_md += f"- {f['suggestion']}\n"
    
    report_md += f"""
---

> 体检时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
> 由 拉小码 AI 生成
"""
    
    return report_md


# ============== 主入口 ==============
async def main(product_url: str) -> str:
    """主入口函数（单个商品体检）"""
    from playwright.async_api import async_playwright
    
    pc_url = get_pc_url(product_url)
    product_id = extract_product_id(pc_url)
    
    if not product_id:
        return "❌ 无法识别京东商品链接"
    
    print(f"正在爬取: {pc_url}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent=PC_UA,
            locale='zh-CN'
        )
        page = await context.new_page()
        
        try:
            await page.goto(pc_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(3000)
            
            await page.evaluate("() => window.scrollTo(0, 500)")
            await page.wait_for_timeout(2000)
            
            # 提取和分析
            product_data = await extract_product_data(page, use_pc=True)
            human_scores, ai_scores = await llm_analyze_dual(product_data)
            fixes = generate_fixes_dual(human_scores, ai_scores)
            
            human_total = sum(human_scores.values()) // len(human_scores)
            ai_total = sum(ai_scores.values()) // len(ai_scores)
            
            print(f"分析完成 - Human: {human_total}/100, AI: {ai_total}/100")
            
        except Exception as e:
            return f"❌ 爬取失败: {str(e)}"
        finally:
            await browser.close()
    
    # 生成报告
    report_md = await generate_feishu_report(product_data, human_scores, ai_scores, fixes, pc_url)
    
    return report_md


async def main_compare(url1: str, url2: str) -> str:
    """对比入口函数"""
    return await compare_products(url1, url2)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) >= 3:
        # 对比模式
        url1 = sys.argv[1]
        url2 = sys.argv[2]
        result = asyncio.run(main_compare(url1, url2))
    else:
        # 单品模式
        url = sys.argv[1] if len(sys.argv) > 1 else "https://item.jd.com/100304875518.html"
        result = asyncio.run(main(url))
    
    print(result)
