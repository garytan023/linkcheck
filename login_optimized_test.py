"""
小红书链接监控工具 - 登录优化版
专门解决登录和反爬问题
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

class LoginOptimizedMonitor:
    def __init__(self):
        self.stop_flag = False
        self.login_wait_time = 60  # 增加到60秒
        self.storage_state_path = "xhs_optimized_storage.json"
        self.user_data_dir = "xhs_optimized_profile"

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        try:
            print(f"[{timestamp}] {message}")
        except UnicodeEncodeError:
            print(f"[{timestamp}] {message.encode('ascii', 'ignore').decode('ascii')}")

    def get_random_delay(self, min_sec, max_sec):
        """获取随机延迟"""
        return random.uniform(min_sec, max_sec)

    def check_login_status(self, page):
        """检查登录状态"""
        try:
            # 综合检测登录状态
            is_logged_in = page.evaluate("""() => {
                // 检查用户头像
                const avatar = document.querySelector('.avatar, .user-avatar, [class*="Avatar"]');
                // 检查用户信息
                const userInfo = document.querySelector('.user-info, .login-info, [class*="UserInfo"]');
                // 检查是否有登录按钮
                const loginBtn = document.querySelector('.login-btn, [class*="login-button"]');
                // 检查Cookie
                const hasCookie = document.cookie.includes('web_session') ||
                                document.cookie.includes('xsecappid');

                // 判断是否已登录
                return (avatar || userInfo) && hasCookie && !loginBtn;
            }""")
            return is_logged_in
        except Exception:
            return False

    def perform_login_with_retry(self, page):
        """带重试的登录流程"""
        self.log("[登录] 开始登录流程...")

        # 1. 打开小红书首页
        try:
            self.log("[登录] 正在打开小红书首页...")
            page.goto('https://www.xiaohongshu.com/', wait_until='domcontentloaded', timeout=30000)
            time.sleep(3)
        except Exception as e:
            self.log(f"[登录] 打开首页失败: {e}")
            page.goto('https://www.xiaohongshu.com/', timeout=30000)
            time.sleep(3)

        # 2. 检查是否已登录
        if self.check_login_status(page):
            self.log("[登录] 已登录，跳过扫码")
            try:
                page.context.storage_state(path=self.storage_state_path)
                self.log("[登录] 登录状态已保存")
            except Exception:
                pass
            return True

        # 3. 执行扫码登录
        self.log("[登录] 未登录，开始扫码...")
        self.log("[登录] 请在浏览器中扫码登录小红书")

        max_wait = self.login_wait_time
        login_success = False

        for remaining in range(max_wait, 0, -5):
            if self.stop_flag:
                break

            self.log(f"[登录] 倒计时: {remaining}秒")

            # 检查登录状态
            if self.check_login_status(page):
                login_success = True
                self.log("[登录] 检测到登录成功！")
                time.sleep(2)
                break

            time.sleep(5)

        # 4. 保存登录状态
        if login_success:
            try:
                page.context.storage_state(path=self.storage_state_path)
                self.log("[登录] 登录状态已保存到文件")
            except Exception as e:
                self.log(f"[登录] 保存登录状态失败: {e}")
        else:
            self.log("[登录] 登录超时，将尝试无登录模式")

        return login_success

    def read_csv_simple(self, csv_file):
        """简单读取CSV"""
        items = []
        try:
            df = pd.read_excel('link.xlsx')
            links = df['link'].tolist()[:1]  # 只测试1个链接

            with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['产品', '序号', '链接'])
                for i, link in enumerate(links, 1):
                    writer.writerow([f'登录测试{i}', str(i), link])

            for i, link in enumerate(links, 1):
                items.append({
                    '产品': f'登录测试{i}',
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

    def check_for_blocking(self, page):
        """检查是否被反爬拦截"""
        try:
            page_content = page.content()
            block_indicators = [
                '访问过于频繁',
                '请求过于频繁',
                '请稍后再试',
                '验证',
                '机器人',
                'captcha',
                '验证码',
                'block',
                'forbidden'
            ]

            for indicator in block_indicators:
                if indicator in page_content.lower():
                    self.log(f"[反爬] 检测到反爬: {indicator}")
                    return True
            return False
        except Exception:
            return False

    def test_with_login_optimization(self, items, screenshot_dir):
        """登录优化版测试"""
        results = []

        self.log("[浏览器] 启动登录优化版浏览器...")

        with sync_playwright() as p:
            try:
                os.makedirs(self.user_data_dir, exist_ok=True)

                context = p.chromium.launch_persistent_context(
                    user_data_dir=self.user_data_dir,
                    headless=False,
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
                )
            except Exception as e:
                self.log(f"启动浏览器失败: {e}")
                raise

            page = context.pages[0] if context.pages else context.new_page()
            page.set_default_timeout(60000)

            # 执行登录
            login_success = self.perform_login_with_retry(page)

            # 处理链接
            for idx, item in enumerate(items, 1):
                if self.stop_flag:
                    break

                link = item.get('链接', '')
                product = item.get('产品', '')
                seq_val = item.get('序号', str(idx))
                name_prefix = self.sanitize_name(f"{product}_{seq_val}")

                self.log(f"[{idx}/{len(items)}] 处理链接: {link[:50]}...")

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
                    '检测时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }

                try:
                    # 访问链接前的随机延迟
                    delay = self.get_random_delay(5, 10)
                    self.log(f"  [延迟] 等待 {delay:.1f} 秒...")
                    time.sleep(delay)

                    # 访问链接
                    self.log(f"  [访问] 正在访问链接...")
                    resp = page.goto(link, wait_until='domcontentloaded', timeout=45000)
                    result['HTTP状态'] = resp.status if resp else ''

                    # 页面加载后的等待
                    page_load_delay = self.get_random_delay(3, 6)
                    self.log(f"  [加载] 页面加载，等待 {page_load_delay:.1f} 秒...")
                    time.sleep(page_load_delay)

                    # 检查反爬
                    if self.check_for_blocking(page):
                        result['反爬状态'] = '触发反爬'
                        result['错误信息'] = '检测到反爬机制'
                        self.log("  [反爬] 检测到反爬机制，可能需要等待更长时间")

                    # 截图
                    screenshot_name = f'{name_prefix}_screenshot.png'
                    screenshot_path = os.path.join(screenshot_dir, screenshot_name)

                    try:
                        page.screenshot(path=screenshot_path, full_page=False)
                        result['截屏文件'] = screenshot_path
                        self.log(f"  [截图] 成功: {screenshot_name}")
                    except Exception as se:
                        self.log(f"  [截图] 失败: {se}")

                    result['采集状态'] = '成功'
                    self.log(f"  [完成] 链接处理成功")

                except Exception as e:
                    result['错误信息'] = str(e)
                    self.log(f"  [错误] 处理失败: {e}")

                results.append(result)

            try:
                context.close()
            except Exception:
                pass
            self.log("[浏览器] 已关闭")

        return results

    def run_optimized_test(self):
        """运行优化测试"""
        print("="*70)
        print("小红书链接监控工具 - 登录优化版测试")
        print("="*70)

        # 1. 准备测试数据
        csv_file = "test_login_optimized.csv"
        try:
            items = self.read_csv_simple(csv_file)
            if not items:
                self.log("没有找到测试数据")
                return False
            self.log(f"读取到 {len(items)} 个测试项目")
        except Exception as e:
            self.log(f"准备测试数据失败: {e}")
            return False

        # 2. 输出目录
        output_dir = "login_optimized_output"
        screenshot_dir = os.path.join(output_dir, 'screenshots')
        os.makedirs(screenshot_dir, exist_ok=True)

        self.log(f"输出目录: {output_dir}")

        # 3. 开始测试
        try:
            self.log("="*60)
            self.log("开始登录优化版测试...")
            self.log("优化内容:")
            self.log("- 增强登录检测和等待")
            self.log("- 随机化时间间隔")
            self.log("- 反爬机制检测")
            self.log("="*60)

            start_time = time.time()
            results = self.test_with_login_optimization(items, screenshot_dir)
            total_time = round(time.time() - start_time, 1)

            # 4. 结果分析
            if results:
                self.log("="*60)
                self.log("登录优化版测试完成!")

                success_count = sum(1 for r in results if r.get('采集状态') == '成功')
                login_count = sum(1 for r in results if r.get('登录状态') == '成功')
                block_count = sum(1 for r in results if r.get('反爬状态') == '触发反爬')

                self.log(f"总计: {len(results)} 条")
                self.log(f"成功: {success_count} 条")
                self.log(f"登录: {login_count} 条")
                self.log(f"反爬触发: {block_count} 条")
                self.log(f"总耗时: {total_time} 秒")
                self.log("="*60)

                # 详细结果
                for result in results:
                    status = "OK" if result['采集状态'] == '成功' else "FAIL"
                    login = "登录" if result['登录状态'] == '成功' else "未登录"
                    anti = "反爬" if result['反爬状态'] == '触发反爬' else "正常"
                    self.log(f"  {status} | {login} | {anti} | {result['产品']}")

                # 保存结果
                with open(os.path.join(output_dir, 'login_optimized_results.json'), 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)

                self.log(f"结果已保存: login_optimized_results.json")
                return True

        except KeyboardInterrupt:
            self.log("\n用户中断")
            return False
        except Exception as e:
            self.log(f"测试失败: {e}")
            return False

if __name__ == "__main__":
    print("登录优化版工具启动...")

    monitor = LoginOptimizedMonitor()

    try:
        success = monitor.run_optimized_test()
        if success:
            print("\n登录优化版测试完成!")
            print("请检查输出目录中的结果")
        else:
            print("\n测试遇到问题")
    except Exception as e:
        print(f"启动失败: {e}")