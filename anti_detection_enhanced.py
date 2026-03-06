"""
小红书链接监控工具 - 反爬优化增强版
重点解决反爬检测和时间间隔优化
"""

import os
import sys
import time
import random
from datetime import datetime
import pandas as pd
import csv
import re
import json
from playwright.sync_api import sync_playwright
from urllib.parse import urljoin

class AntiDetectionEnhancedMonitor:
    def __init__(self):
        self.stop_flag = False
        self.login_wait_time = 30

        # 反爬优化配置
        self.config = {
            # 时间间隔配置（秒）
            'delays': {
                'link_interval': (3, 8),          # 链接间延迟：3-8秒随机
                'page_load': (2, 5),              # 页面加载后等待：2-5秒
                'screenshot': (1, 3),             # 截图前等待：1-3秒
                'login_check': (2, 4),            # 登录检查间隔：2-4秒
                'api_request': (1, 2),            # API请求间隔：1-2秒
                'scroll': (0.5, 1.5),             # 滚动操作间隔：0.5-1.5秒
            },
            # 浏览器配置
            'browser': {
                'viewport': [(1920, 1080), (1680, 1050), (1440, 900)],
                'user_agents': [
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
                ]
            },
            # 请求头配置
            'headers': {
                'accept': ['text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8'],
                'accept_language': ['zh-CN,zh;q=0.9,en;q=0.8', 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2'],
                'accept_encoding': ['gzip, deflate, br', 'gzip, deflate'],
                'sec_fetch_dest': ['document', 'empty'],
                'sec_fetch_mode': ['navigate', 'cors'],
                'sec_fetch_site': ['none', 'same-site']
            }
        }

        self.storage_state_path = "xhs_anti_detection_storage.json"
        self.user_data_dir = "xhs_anti_detection_profile"

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        try:
            print(f"[{timestamp}] {message}")
        except UnicodeEncodeError:
            print(f"[{timestamp}] {message.encode('ascii', 'ignore').decode('ascii')}")

    def get_random_delay(self, delay_type):
        """获取随机延迟时间"""
        min_delay, max_delay = self.config['delays'][delay_type]
        return random.uniform(min_delay, max_delay)

    def get_random_headers(self):
        """获取随机请求头"""
        headers = {}

        # 随机选择User-Agent
        headers['user-agent'] = random.choice(self.config['browser']['user_agents'])

        # 随机选择其他头部
        for key, values in self.config['headers'].items():
            if random.random() > 0.3:  # 70%概率包含该头部
                headers[key.replace('_', '-')] = random.choice(values)

        return headers

    def human_like_scroll(self, page):
        """模拟人类滚动行为"""
        try:
            # 随机滚动次数和距离
            scroll_count = random.randint(2, 4)

            for i in range(scroll_count):
                # 随机滚动距离
                scroll_distance = random.randint(200, 800)
                scroll_direction = random.choice(['down', 'up'])

                if scroll_direction == 'down':
                    page.evaluate(f"() => window.scrollBy(0, {scroll_distance})")
                else:
                    page.evaluate(f"() => window.scrollBy(0, -{scroll_distance})")

                # 随机等待时间
                time.sleep(self.get_random_delay('scroll'))

            # 最终回到顶部
            page.evaluate("() => window.scrollTo(0, 0)")
            time.sleep(self.get_random_delay('scroll'))

        except Exception as e:
            self.log(f"  [滚动] 滚动操作失败: {e}")

    def detect_anti_crawler(self, page):
        """检测反爬虫机制"""
        try:
            # 检查常见的反爬虫页面元素
            anti_crawler_indicators = page.evaluate("""() => {
                const indicators = {
                    hasCaptcha: !!document.querySelector('.captcha, [class*="captcha"], [class*="verify"]'),
                    hasBlockPage: !!document.querySelector('[class*="block"], [class*="forbidden"], [class*="access-denied"]'),
                    hasRateLimit: !!document.querySelector('[class*="rate-limit"], [class*="too-many"]'),
                    hasVerification: !!document.querySelector('[class*="verification"], [class*="verify"]'),
                    blockText: document.body.innerText.includes('访问过于频繁') ||
                              document.body.innerText.includes('请求过于频繁') ||
                              document.body.innerText.includes('请稍后再试') ||
                              document.body.innerText.includes('验证') ||
                              document.body.innerText.includes('机器人') ||
                              document.body.innerText.includes('机器人检测'),
                    title: document.title
                };

                return indicators;
            }""")

            # 判断是否被反爬虫拦截
            is_blocked = (
                anti_crawler_indicators['hasCaptcha'] or
                anti_crawler_indicators['hasBlockPage'] or
                anti_crawler_indicators['hasRateLimit'] or
                anti_crawler_indicators['hasVerification'] or
                anti_crawler_indicators['blockText']
            )

            if is_blocked:
                self.log(f"  [反爬检测] ⚠️ 检测到反爬机制: {anti_crawler_indicators}")
                return True, anti_crawler_indicators

            return False, anti_crawler_indicators

        except Exception as e:
            self.log(f"  [反爬检测] 检测失败: {e}")
            return False, {}

    def handle_anti_crawler(self, page, indicators):
        """处理反爬虫情况"""
        self.log("  [反爬处理] 🛡️ 检测到反爬，开始处理...")

        try:
            # 策略1: 延长等待时间
            wait_time = random.randint(30, 60)
            self.log(f"  [反爬处理] ⏳ 等待 {wait_time} 秒...")
            time.sleep(wait_time)

            # 策略2: 刷新页面
            self.log("  [反爬处理] 🔄 刷新页面...")
            page.reload(wait_until='domcontentloaded', timeout=30000)
            time.sleep(self.get_random_delay('page_load'))

            # 策略3: 模拟人类行为
            self.log("  [反爬处理] 👤 模拟人类行为...")
            self.human_like_scroll(page)

            # 策略4: 再次检测
            is_blocked, new_indicators = self.detect_anti_crawler(page)
            if not is_blocked:
                self.log("  [反爬处理] ✅ 反爬处理成功")
                return True
            else:
                self.log("  [反爬处理] ❌ 反爬处理失败，建议停止程序")
                return False

        except Exception as e:
            self.log(f"  [反爬处理] 处理异常: {e}")
            return False

    def enhanced_goto(self, page, url, max_retries=3):
        """增强版页面访问，包含反爬检测"""
        for attempt in range(max_retries):
            try:
                self.log(f"  [访问] 尝试访问 {url[:60]}... (第{attempt+1}次)")

                # 随机等待
                if attempt > 0:
                    wait_time = random.randint(5, 15)
                    self.log(f"  [访问] 等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)

                # 访问页面
                resp = page.goto(url, wait_until='domcontentloaded', timeout=45000)

                # 随机等待页面加载
                page_load_delay = self.get_random_delay('page_load')
                self.log(f"  [访问] 页面加载，等待 {page_load_delay:.1f} 秒...")
                time.sleep(page_load_delay)

                # 检测反爬虫
                is_blocked, indicators = self.detect_anti_crawler(page)

                if is_blocked:
                    # 尝试处理反爬虫
                    if attempt < max_retries - 1:
                        self.handle_anti_crawler(page, indicators)
                        continue
                    else:
                        raise Exception("触发反爬虫机制且无法处理")

                # 模拟人类行为
                if random.random() > 0.5:  # 50%概率模拟人类行为
                    self.log("  [访问] 模拟人类滚动行为...")
                    self.human_like_scroll(page)

                self.log(f"  [访问] ✅ 访问成功 (状态码: {resp.status})")
                return resp

            except Exception as e:
                self.log(f"  [访问] ❌ 访问失败 (第{attempt+1}次): {e}")
                if attempt == max_retries - 1:
                    raise e

    def check_login_state_enhanced(self, page):
        """增强版登录状态检测"""
        try:
            login_check = page.evaluate("""() => {
                // 多维度检测
                const checks = {
                    // DOM元素检测
                    hasAvatar: !!document.querySelector('.avatar, .user-avatar, [class*="Avatar"], [class*="user-photo"]'),
                    hasUserInfo: !!document.querySelector('.user-info, .login-info, [class*="UserInfo"], [class*="nickname"]'),
                    hasLoginBtn: !!document.querySelector('.login-btn, [class*="login-button"], button:has-text("登录")'),

                    // Cookie检测
                    cookies: document.cookie,
                    hasWebSession: document.cookie.includes('web_session'),
                    hasXsecAppid: document.cookie.includes('xsecappid'),
                    hasA1: document.cookie.includes('a1'),

                    // 页面内容检测
                    title: document.title,
                    bodyText: document.body.innerText.substring(0, 500),
                    isLoginPage: document.body.innerText.includes('登录') || document.body.innerText.includes('扫码'),

                    // URL检测
                    currentUrl: window.location.href,
                    isXhsDomain: window.location.hostname.includes('xiaohongshu.com')
                };

                // 综合判断
                checks.isLoggedIn = (
                    checks.isXhsDomain &&
                    (checks.hasAvatar || checks.hasUserInfo) &&
                    (checks.hasWebSession || checks.hasXsecAppid) &&
                    !checks.hasLoginBtn &&
                    !checks.isLoginPage
                );

                return checks;
            }""")

            return login_check
        except Exception as e:
            self.log(f"  [登录检测] 检测失败: {e}")
            return {'isLoggedIn': False}

    def read_items_from_csv(self, csv_file):
        """读取CSV文件"""
        items = []
        try:
            with open(csv_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for idx, row in enumerate(reader, 1):
                    link = (row.get('链接') or row.get(reader.fieldnames[0]) or '').strip()
                    if link:
                        product = (row.get('产品') or '').strip()
                        seq = (row.get('序号') or '').strip() or str(idx)
                        items.append({'产品': product, '序号': seq, '链接': link})
        except Exception:
            try:
                with open(csv_file, 'r', encoding='utf-8-sig') as f:
                    reader = csv.reader(f)
                    rows = list(reader)
                    for idx, row in enumerate(rows[1:], 1):
                        if row and len(row) > 0 and row[0].strip():
                            items.append({'产品': '', '序号': str(idx), '链接': row[0].strip()})
            except Exception:
                pass
        return items

    def sanitize_name(self, name):
        try:
            safe = re.sub(r'[^0-9A-Za-z\u4e00-\u9fff]+', '_', name)
            return safe.strip('_') or "item"
        except Exception:
            return "item"

    def extract_note_id(self, url):
        try:
            match = re.search(r'/explore/([a-zA-Z0-9]+)', url)
            if match:
                return match.group(1)
        except:
            pass
        return ''

    def anti_detection_monitor(self, items, screenshot_dir):
        """反爬检测增强版监控"""
        results = []
        covers_dir = os.path.join(screenshot_dir, 'covers')
        os.makedirs(covers_dir, exist_ok=True)

        self.log("[浏览器] 启动反爬检测增强版浏览器...")

        with sync_playwright() as p:
            try:
                os.makedirs(self.user_data_dir, exist_ok=True)

                # 随机选择视窗大小
                viewport = random.choice(self.config['browser']['viewport'])
                user_agent = random.choice(self.config['browser']['user_agents'])

                self.log(f"[浏览器] 视窗: {viewport}, User-Agent: {user_agent[:50]}...")

                context = p.chromium.launch_persistent_context(
                    user_data_dir=self.user_data_dir,
                    headless=False,
                    viewport={'width': viewport[0], 'height': viewport[1]},
                    user_agent=user_agent,
                    ignore_https_errors=True,  # 忽略HTTPS错误
                )
            except Exception as e:
                self.log(f"[错误] 无法启动浏览器: {e}")
                raise

            page = context.pages[0] if context.pages else context.new_page()
            page.set_default_timeout(60000)

            # 设置额外请求头
            page.set_extra_http_headers(self.get_random_headers())

            # 处理每个链接
            for idx, item in enumerate(items, 1):
                if self.stop_flag:
                    self.log("[停止] 用户中断")
                    break

                link = item.get('链接', '')
                product = item.get('产品', '')
                seq_val = item.get('序号', str(idx))
                name_prefix = self.sanitize_name(f"{product}_{seq_val}")

                self.log(f"[{idx}/{len(items)}] 📱 处理: {link[:50]}...")

                result = {
                    '序号': seq_val,
                    '产品': product,
                    '链接': link,
                    '笔记ID': self.extract_note_id(link),
                    '采集状态': '失败',
                    '错误信息': '',
                    'HTTP状态': '',
                    '截屏文件': '',
                    '反爬检测': '未触发',
                    '检测时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    '处理时间': 0
                }

                start_time = time.time()

                try:
                    # 使用增强版访问
                    resp = self.enhanced_goto(page, link)
                    result['HTTP状态'] = resp.status if resp else ''

                    # 截图前的随机等待
                    screenshot_delay = self.get_random_delay('screenshot')
                    self.log(f"  [截图] 等待 {screenshot_delay:.1f} 秒后截图...")
                    time.sleep(screenshot_delay)

                    # 截图
                    screenshot_name = f'{name_prefix}_screenshot.png'
                    screenshot_path = os.path.join(screenshot_dir, screenshot_name)

                    try:
                        page.screenshot(path=screenshot_path, full_page=False)
                        result['截屏文件'] = screenshot_path
                        self.log(f"  ✅ 截图成功: {screenshot_name}")
                    except Exception as se:
                        self.log(f"  ⚠️ 截图失败: {se}")

                    result['采集状态'] = '成功'
                    result['处理时间'] = round(time.time() - start_time, 1)
                    self.log(f"  ✅ 处理完成 (耗时: {result['处理时间']}秒)")

                except Exception as e:
                    result['错误信息'] = str(e)
                    result['处理时间'] = round(time.time() - start_time, 1)

                    if "反爬" in str(e) or "captcha" in str(e).lower():
                        result['反爬检测'] = '触发'

                    self.log(f"  ❌ 处理失败: {e}")

                results.append(result)

                # 链接间的随机延迟
                if idx < len(items):
                    link_delay = self.get_random_delay('link_interval')
                    self.log(f"  [延迟] 等待 {link_delay:.1f} 秒后处理下一个链接...")
                    time.sleep(link_delay)

            try:
                context.close()
            except Exception:
                pass
            self.log("[关闭] 浏览器已关闭")

        return results

    def run_anti_detection_test(self):
        """运行反爬检测测试"""
        print("="*80)
        print("小红书链接监控工具 - 反爬检测增强版测试")
        print("="*80)

        # 1. 准备测试数据
        csv_file = "test_links_anti_detection.csv"
        if not os.path.exists(csv_file):
            try:
                df = pd.read_excel('link.xlsx')
                links = df['link'].tolist()[:2]  # 只测试2个链接

                with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['产品', '序号', '链接'])
                    for i, link in enumerate(links, 1):
                        writer.writerow([f'反爬测试{i}', str(i), link])

                self.log(f"✅ 创建测试CSV: {csv_file}")
            except Exception as e:
                self.log(f"❌ 创建测试数据失败: {e}")
                return False

        # 2. 读取测试数据
        try:
            items = self.read_items_from_csv(csv_file)
            self.log(f"📋 读取到 {len(items)} 个测试项目")
        except Exception as e:
            self.log(f"❌ 读取测试数据失败: {e}")
            return False

        # 3. 设置输出目录
        output_dir = "anti_detection_test_output"
        screenshot_dir = os.path.join(output_dir, 'screenshots')
        os.makedirs(screenshot_dir, exist_ok=True)

        self.log(f"📁 输出目录: {output_dir}")

        # 4. 显示配置信息
        self.log("="*60)
        self.log("🛡️ 反爬检测配置:")
        self.log(f"   链接间隔: {self.config['delays']['link_interval'][0]}-{self.config['delays']['link_interval'][1]}秒")
        self.log(f"   页面加载: {self.config['delays']['page_load'][0]}-{self.config['delays']['page_load'][1]}秒")
        self.log(f"   截图等待: {self.config['delays']['screenshot'][0]}-{self.config['delays']['screenshot'][1]}秒")
        self.log(f"   浏览器视窗: {self.config['browser']['viewport']}")
        self.log("="*60)

        # 5. 开始测试
        try:
            self.log("🚀 开始反爬检测增强版测试...")

            start_time = time.time()
            results = self.anti_detection_monitor(items, screenshot_dir)
            total_time = round(time.time() - start_time, 1)

            # 6. 生成报告
            if results:
                self.log("="*60)
                self.log("✅ 反爬检测测试完成！")

                success_count = sum(1 for r in results if r.get('采集状态') == '成功')
                blocked_count = sum(1 for r in results if r.get('反爬检测') == '触发')
                avg_time = sum(r.get('处理时间', 0) for r in results) / len(results)

                self.log(f"📊 总计: {len(results)} 条")
                self.log(f"✅ 成功: {success_count} 条")
                self.log(f"🛡️ 反爬触发: {blocked_count} 条")
                self.log(f"⏱️ 总耗时: {total_time} 秒")
                self.log(f"⏱️ 平均耗时: {avg_time:.1f} 秒/条")
                self.log("="*60)

                # 详细结果
                for result in results:
                    status = "✅" if result['采集状态'] == '成功' else "❌"
                    anti = "🛡️" if result['反爬检测'] == '触发' else "✓"
                    self.log(f"   {status} {anti} {result['产品']} - {result['处理时间']}秒")

                # 保存结果
                with open(os.path.join(output_dir, 'anti_detection_results.json'), 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)

                self.log(f"📄 结果已保存: anti_detection_results.json")
                return True

        except KeyboardInterrupt:
            self.log("\n⚠️ 测试被用户中断")
            return False
        except Exception as e:
            self.log(f"❌ 测试失败: {e}")
            return False

if __name__ == "__main__":
    print("反爬检测增强版测试工具启动...")

    monitor = AntiDetectionEnhancedMonitor()

    try:
        success = monitor.run_anti_detection_test()
        if success:
            print("\n🎉 反爬检测测试成功！")
            print("请检查输出目录中的结果和分析")
        else:
            print("\n❌ 测试遇到问题")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")