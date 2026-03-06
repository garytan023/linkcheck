"""
小红书链接监控工具 - 最终完整版
解决登录检测和反爬问题的最终方案
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

class FinalCompleteMonitor:
    def __init__(self):
        self.stop_flag = False
        self.storage_state_path = "xhs_final_storage.json"
        self.user_data_dir = "xhs_final_profile"

        # 优化的时间配置
        self.delays = {
            'login_check': 3,          # 登录检查间隔
            'link_interval': (8, 15),   # 链接间延迟：8-15秒
            'page_load': (5, 10),       # 页面加载后等待：5-10秒
            'screenshot': (2, 4),       # 截图前等待：2-4秒
        }

        self.log("小红书链接监控工具 - 最终完整版启动")

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        try:
            print(f"[{timestamp}] {message}")
        except UnicodeEncodeError:
            print(f"[{timestamp}] {message.encode('ascii', 'ignore').decode('ascii')}")

    def check_login_comprehensive(self, page):
        """全面的登录状态检查"""
        try:
            # 多重检查登录状态
            login_state = page.evaluate("""() => {
                const checks = {
                    // DOM元素检查
                    hasAvatar: !!document.querySelector('.avatar, .user-avatar, [class*="Avatar"], [class*="user-photo"]'),
                    hasUserInfo: !!document.querySelector('.user-info, .login-info, [class*="UserInfo"], [class*="nickname"]'),
                    hasLoginBtn: !!document.querySelector('.login-btn, [class*="login-button"], button:has-text("登录"), .login-box'),

                    // Cookie检查
                    cookies: document.cookie,
                    hasWebSession: document.cookie.includes('web_session'),
                    hasXsecAppid: document.cookie.includes('xsecappid'),
                    hasA1: document.cookie.includes('a1'),

                    // 页面内容检查
                    title: document.title,
                    isLoginPage: document.body.innerText.includes('登录') || document.body.innerText.includes('扫码'),

                    // URL检查
                    currentUrl: window.location.href,
                    isXhsDomain: window.location.hostname.includes('xiaohongshu.com')
                };

                // 综合判断登录状态
                checks.isLoggedIn = (
                    checks.isXhsDomain &&
                    (checks.hasAvatar || checks.hasUserInfo) &&
                    (checks.hasWebSession || checks.hasXsecAppid) &&
                    !checks.hasLoginBtn &&
                    !checks.isLoginPage
                );

                return checks;
            }""")

            return login_state
        except Exception as e:
            self.log(f"  登录检查异常: {e}")
            return {'isLoggedIn': False}

    def perform_complete_login(self, page):
        """完整登录流程"""
        self.log("[登录] ===== 开始完整登录流程 =====")

        # 1. 打开小红书首页
        try:
            self.log("[登录] 步骤1: 打开小红书首页...")
            page.goto('https://www.xiaohongshu.com/', wait_until='domcontentloaded', timeout=30000)
            time.sleep(5)
        except Exception as e:
            self.log(f"[登录] 打开首页失败: {e}")
            return False

        # 2. 检查已有登录状态
        self.log("[登录] 步骤2: 检查已有登录状态...")
        login_state = self.check_login_comprehensive(page)

        if login_state.get('isLoggedIn', False):
            self.log("[登录] ✓ 已检测到登录状态")
            self.log(f"[登录] - 头像: {login_state.get('hasAvatar', False)}")
            self.log(f"[登录] - Cookie: {login_state.get('hasWebSession', False)}")

            # 保存登录状态
            try:
                page.context.storage_state(path=self.storage_state_path)
                self.log("[登录] ✓ 登录状态已保存")
            except Exception as e:
                self.log(f"[登录] 保存状态失败: {e}")

            return True

        # 3. 手动扫码登录
        self.log("[登录] 步骤3: 需要扫码登录")
        self.log("[登录] ============ 重要提示 ============")
        self.log("[登录] 请在浏览器中完成以下步骤:")
        self.log("[登录] 1. 使用小红书App扫描二维码")
        self.log("[登录] 2. 在手机上确认登录")
        self.log("[登录] 3. 等待页面自动跳转")
        self.log("[登录] ===============================")

        max_wait_time = 120  # 增加到2分钟
        login_success = False

        for remaining in range(max_wait_time, 0, -self.delays['login_check']):
            if self.stop_flag:
                break

            # 每15秒显示一次详细状态
            if remaining % 15 == 0:
                current_state = self.check_login_comprehensive(page)
                self.log(f"[登录] 倒计时: {remaining}秒 | 状态检查...")
                self.log(f"[登录] - 登录按钮: {current_state.get('hasLoginBtn', 'Unknown')}")
                self.log(f"[登录] - 登录页面: {current_state.get('isLoginPage', 'Unknown')}")

            # 检查登录状态
            if self.check_login_comprehensive(page).get('isLoggedIn', False):
                login_success = True
                self.log("[登录] ✓ 检测到登录成功！")
                time.sleep(3)  # 等待登录完全稳定
                break

            time.sleep(self.delays['login_check'])

        # 4. 最终确认和保存
        if login_success:
            self.log("[登录] ✓ 登录成功，正在保存状态...")
            try:
                page.context.storage_state(path=self.storage_state_path)
                self.log("[登录] ✓ 登录状态已保存到文件")
            except Exception as e:
                self.log(f"[登录] ⚠️ 保存登录状态失败: {e}")
        else:
            self.log("[登录] ❌ 登录超时，将使用无登录模式")

        return login_success

    def read_csv_data(self, csv_file):
        """读取CSV数据"""
        items = []
        try:
            df = pd.read_excel('link.xlsx')
            links = df['link'].tolist()[:1]  # 只测试1个链接进行验证

            with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['产品', '序号', '链接'])
                for i, link in enumerate(links, 1):
                    writer.writerow([f'最终测试{i}', str(i), link])

            for i, link in enumerate(links, 1):
                items.append({
                    '产品': f'最终测试{i}',
                    '序号': str(i),
                    '链接': link
                })
        except Exception as e:
            self.log(f"读取CSV失败: {e}")
        return items

    def sanitize_name(self, name):
        """清理文件名"""
        try:
            safe = re.sub(r'[^0-9A-Za-z\u4e00-\u9fff]+', '_', name)
            return safe.strip('_') or "item"
        except Exception:
            return "item"

    def extract_note_id(self, url):
        """提取笔记ID"""
        try:
            match = re.search(r'/explore/([a-zA-Z0-9]+)', url)
            if match:
                return match.group(1)
        except:
            pass
        return ''

    def final_test_with_complete_features(self, items, screenshot_dir):
        """最终完整版测试"""
        results = []

        self.log("[启动] ===== 启动最终完整版测试 =====")

        with sync_playwright() as p:
            try:
                os.makedirs(self.user_data_dir, exist_ok=True)

                # 创建浏览器上下文
                context = p.chromium.launch_persistent_context(
                    user_data_dir=self.user_data_dir,
                    headless=False,
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
                )

                # 设置额外的请求头
                context.set_extra_http_headers({
                    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
                    'accept-encoding': 'gzip, deflate, br',
                    'sec-fetch-dest': 'document',
                    'sec-fetch-mode': 'navigate',
                    'sec-fetch-site': 'none'
                })

            except Exception as e:
                self.log(f"启动浏览器失败: {e}")
                raise

            page = context.pages[0] if context.pages else context.new_page()
            page.set_default_timeout(60000)

            # 执行完整登录
            login_success = self.perform_complete_login(page)

            # 处理链接
            for idx, item in enumerate(items, 1):
                if self.stop_flag:
                    break

                link = item.get('链接', '')
                product = item.get('产品', '')
                seq_val = item.get('序号', str(idx))
                name_prefix = self.sanitize_name(f"{product}_{seq_val}")

                self.log(f"[{idx}/{len(items)}] ===== 处理链接 {idx} =====")
                self.log(f"[{idx}/{len(items)}] 链接: {link[:60]}...")

                result = {
                    '序号': seq_val,
                    '产品': product,
                    '链接': link,
                    '笔记ID': self.extract_note_id(link),
                    '采集状态': '失败',
                    '错误信息': '',
                    'HTTP状态': '',
                    '截屏文件': '',
                    '登录状态': '成功' if login_success else '未登录',
                    '反爬状态': '正常',
                    '检测时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    '处理时间': 0
                }

                start_time = time.time()

                try:
                    # 链接间延迟
                    if idx > 1:
                        delay = random.uniform(*self.delays['link_interval'])
                        self.log(f"  [延迟] 链接间延迟 {delay:.1f} 秒...")
                        time.sleep(delay)

                    # 访问链接
                    self.log(f"  [访问] 正在访问链接...")
                    resp = page.goto(link, wait_until='domcontentloaded', timeout=45000)
                    result['HTTP状态'] = resp.status if resp else ''

                    # 页面加载等待
                    page_load_delay = random.uniform(*self.delays['page_load'])
                    self.log(f"  [加载] 页面加载等待 {page_load_delay:.1f} 秒...")
                    time.sleep(page_load_delay)

                    # 检查反爬和登录弹窗
                    page_content = page.content()
                    anti_crawler_indicators = [
                        '访问过于频繁', '请求过于频繁', '请稍后再试',
                        '验证码', '验证', '机器人', 'captcha'
                    ]

                    login_popup_indicators = [
                        '登录', '扫码', '请登录', 'login-modal'
                    ]

                    for indicator in anti_crawler_indicators:
                        if indicator in page_content:
                            result['反爬状态'] = '触发反爬'
                            result['错误信息'] = f'检测到反爬: {indicator}'
                            self.log(f"  [反爬] ⚠️ 检测到反爬: {indicator}")
                            break

                    if '登录' in page_content and '扫码' in page_content:
                        result['登录状态'] = '需要重新登录'
                        self.log(f"  [登录] ⚠️ 检测到登录弹窗")

                    # 截图
                    screenshot_delay = random.uniform(*self.delays['screenshot'])
                    self.log(f"  [截图] 截图前等待 {screenshot_delay:.1f} 秒...")
                    time.sleep(screenshot_delay)

                    screenshot_name = f'{name_prefix}_screenshot.png'
                    screenshot_path = os.path.join(screenshot_dir, screenshot_name)

                    try:
                        page.screenshot(path=screenshot_path, full_page=False)
                        result['截屏文件'] = screenshot_path

                        # 检查截图文件
                        if os.path.exists(screenshot_path) and os.path.getsize(screenshot_path) > 1000:
                            self.log(f"  [截图] ✓ 截图成功: {screenshot_name} ({os.path.getsize(screenshot_path)} bytes)")
                        else:
                            self.log(f"  [截图] ⚠️ 截图可能有问题: {screenshot_name}")

                    except Exception as se:
                        self.log(f"  [截图] ❌ 截图失败: {se}")

                    if result['采集状态'] == '失败' and not result['错误信息']:
                        result['采集状态'] = '成功'

                    result['处理时间'] = round(time.time() - start_time, 1)
                    self.log(f"  [完成] ✓ 链接处理完成 (耗时: {result['处理时间']}秒)")

                except Exception as e:
                    result['错误信息'] = str(e)
                    result['处理时间'] = round(time.time() - start_time, 1)
                    self.log(f"  [错误] ❌ 处理失败: {e}")

                results.append(result)

            try:
                context.close()
            except Exception:
                pass
            self.log("[关闭] 浏览器已关闭")

        return results

    def run_final_complete_test(self):
        """运行最终完整版测试"""
        print("="*80)
        print("小红书链接监控工具 - 最终完整版")
        print("="*80)

        # 1. 准备测试数据
        csv_file = "test_final_complete.csv"
        try:
            items = self.read_csv_data(csv_file)
            if not items:
                self.log("❌ 没有找到测试数据")
                return False
            self.log(f"✅ 读取到 {len(items)} 个测试项目")
        except Exception as e:
            self.log(f"❌ 准备测试数据失败: {e}")
            return False

        # 2. 输出目录
        output_dir = "final_complete_output"
        screenshot_dir = os.path.join(output_dir, 'screenshots')
        os.makedirs(screenshot_dir, exist_ok=True)

        self.log(f"📁 输出目录: {output_dir}")

        # 3. 显示配置
        self.log("="*60)
        self.log("🔧 最终完整版配置:")
        self.log(f"   登录检查间隔: {self.delays['login_check']}秒")
        self.log(f"   链接间延迟: {self.delays['link_interval'][0]}-{self.delays['link_interval'][1]}秒")
        self.log(f"   页面加载等待: {self.delays['page_load'][0]}-{self.delays['page_load'][1]}秒")
        self.log(f"   截图前等待: {self.delays['screenshot'][0]}-{self.delays['screenshot'][1]}秒")
        self.log("="*60)

        # 4. 开始测试
        try:
            self.log("🚀 开始最终完整版测试...")

            start_time = time.time()
            results = self.final_test_with_complete_features(items, screenshot_dir)
            total_time = round(time.time() - start_time, 1)

            # 5. 结果分析
            if results:
                self.log("="*60)
                self.log("🎉 最终完整版测试完成!")

                success_count = sum(1 for r in results if r.get('采集状态') == '成功')
                login_count = sum(1 for r in results if r.get('登录状态') == '成功')
                block_count = sum(1 for r in results if r.get('反爬状态') == '触发反爬')
                avg_time = sum(r.get('处理时间', 0) for r in results) / len(results)

                self.log(f"📊 测试统计:")
                self.log(f"   总计: {len(results)} 条")
                self.log(f"   成功: {success_count} 条")
                self.log(f"   登录: {login_count} 条")
                self.log(f"   反爬触发: {block_count} 条")
                self.log(f"   总耗时: {total_time} 秒")
                self.log(f"   平均耗时: {avg_time:.1f} 秒/条")
                self.log("="*60)

                # 详细结果
                for result in results:
                    status = "✅" if result['采集状态'] == '成功' else "❌"
                    login = "🔐" if result['登录状态'] == '成功' else "🔓"
                    anti = "🛡️" if result['反爬状态'] == '触发反爬' else "✓"
                    self.log(f"   {status} {login} {anti} {result['产品']} ({result['处理时间']}s)")

                    if result.get('截屏文件'):
                        screenshot_path = result['截屏_file']
                        if os.path.exists(screenshot_path):
                            file_size = os.path.getsize(screenshot_path)
                            self.log(f"      📸 截图: {os.path.basename(screenshot_path)} ({file_size} bytes)")
                        else:
                            self.log(f"      📸 截图: 文件不存在")

                # 保存结果
                with open(os.path.join(output_dir, 'final_complete_results.json'), 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)

                self.log(f"\n📄 结果已保存: final_complete_results.json")
                self.log(f"📁 截图目录: {screenshot_dir}")
                return True

        except KeyboardInterrupt:
            self.log("\n⚠️ 用户中断")
            return False
        except Exception as e:
            self.log(f"❌ 测试失败: {e}")
            import traceback
            self.log(f"详细错误: {traceback.format_exc()}")
            return False

if __name__ == "__main__":
    print("最终完整版工具启动...")

    monitor = FinalCompleteMonitor()

    try:
        success = monitor.run_final_complete_test()
        if success:
            print("\n🎉 最终完整版测试成功完成!")
            print("✅ 请检查输出目录中的结果和截图")
        else:
            print("\n❌ 测试遇到问题")
    except Exception as e:
        print(f"❌ 启动失败: {e}")