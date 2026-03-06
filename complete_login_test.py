"""
小红书链接监控工具 - 完整登录版修复
包含完整的扫码登录实现
"""

import os
import sys
import time
from datetime import datetime
import pandas as pd
import csv
import re
import json
from playwright.sync_api import sync_playwright
from urllib.parse import urljoin

class CompleteLoginFixedMonitor:
    def __init__(self):
        self.stop_flag = False
        self.login_wait_time = 30
        self.storage_state_path = "xhs_complete_storage.json"
        self.user_data_dir = "xhs_complete_profile"
        self.http_user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
        )

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        try:
            print(f"[{timestamp}] {message}")
        except UnicodeEncodeError:
            print(f"[{timestamp}] {message.encode('ascii', 'ignore').decode('ascii')}")

    def read_items_from_csv(self, csv_file):
        """读取CSV文件"""
        items = []
        try:
            with open(csv_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                if reader.fieldnames and ('链接' in reader.fieldnames or reader.fieldnames[0]):
                    for idx, row in enumerate(reader, 1):
                        link = (row.get('链接') or row.get(reader.fieldnames[0]) or '').strip()
                        if not link:
                            continue
                        product = (row.get('产品') or '').strip()
                        seq = (row.get('序号') or '').strip() or str(idx)
                        items.append({'产品': product, '序号': seq, '链接': link})
        except Exception:
            # 兼容旧格式：单列链接
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

    def check_login_state(self, page):
        """检查登录状态"""
        try:
            # 检查登录状态的多种方法
            login_check = page.evaluate("""() => {
                // 方法1: 检查用户头像
                const avatar = document.querySelector('.avatar, .user-avatar, [class*="Avatar"]');
                // 方法2: 检查用户信息
                const userInfo = document.querySelector('.user-info, .login-info, [class*="UserInfo"]');
                // 方法3: 检查登录按钮存在
                const loginBtn = document.querySelector('.login-btn, [class*="login-button"], button:has-text("登录"), [data-testid*="login"]');
                // 方法4: 检查登录相关Cookie
                const hasCookie = document.cookie.includes('web_session') ||
                               document.cookie.includes('xsecappid') ||
                               document.cookie.includes('a1');
                // 方法5: 检查页面是否显示登录界面
                const isLoginPage = document.body.innerText.includes('登录') ||
                                   document.body.innerText.includes('扫码') ||
                                   document.querySelector('[class*="login"], [class*="qr"]');

                return {
                    hasAvatar: !!avatar,
                    hasUserInfo: !!userInfo,
                    hasLoginBtn: !!loginBtn,
                    hasCookie: hasCookie,
                    isLoginPage: isLoginPage,
                    isLoggedIn: (avatar || userInfo) && hasCookie && !loginBtn && !isLoginPage
                };
            }""")

            return login_check
        except Exception as e:
            self.log(f"  登录状态检查失败: {e}")
            return {'isLoggedIn': False}

    def perform_login(self, page):
        """执行完整的登录流程"""
        self.log("[登录] 开始小红书登录流程...")

        # 1. 打开小红书首页
        try:
            self.log("[登录] 正在打开小红书首页...")
            page.goto('https://www.xiaohongshu.com/', wait_until='domcontentloaded', timeout=30000)
            time.sleep(3)
        except Exception as e:
            self.log(f"[登录] 打开首页失败: {e}")
            page.goto('https://www.xiaohongshu.com/', timeout=30000)
            time.sleep(3)

        # 2. 检查已有登录状态
        try:
            cookies = page.context.cookies()
            has_auth_cookie = any(
                c.get("name") in ["a1", "web_session", "a1.sig"] and "xiaohongshu.com" in (c.get("domain") or "")
                for c in cookies
            )
            if has_auth_cookie:
                self.log("[登录] 检测到历史登录Cookie")
        except Exception:
            pass

        # 3. 检查当前登录状态
        login_state = self.check_login_state(page)
        if login_state.get('isLoggedIn', False):
            self.log("[登录] ✅ 已登录，无需扫码")
            try:
                page.context.storage_state(path=self.storage_state_path)
                self.log("[登录] 登录状态已保存")
            except Exception:
                pass
            return True

        # 4. 显示登录界面，等待用户扫码
        self.log("[登录] ⚠️ 未检测到登录，请扫码登录")
        self.log("[登录] 💡 请在浏览器中完成扫码登录")

        # 等待登录的倒计时
        wait_seconds = self.login_wait_time
        login_success = False

        for remaining in range(wait_seconds, 0, -1):
            if self.stop_flag:
                break

            # 每5秒检查一次登录状态
            if remaining % 5 == 0 or remaining <= 5:
                self.log(f"[登录] ⏳ 倒计时: {remaining}秒")

                try:
                    current_state = self.check_login_state(page)
                    if current_state.get('isLoggedIn', False):
                        login_success = True
                        self.log("[登录] ✅ 检测到登录成功！")
                        time.sleep(2)
                        break

                    # 详细状态日志
                    if remaining == wait_seconds or remaining <= 10:
                        self.log(f"[登录] 状态: 头像={current_state.get('hasAvatar', False)}, "
                               f"用户信息={current_state.get('hasUserInfo', False)}, "
                               f"登录页={current_state.get('isLoginPage', False)}")

                except Exception as e:
                    self.log(f"[登录] 检查状态失败: {e}")

            time.sleep(1)

        # 5. 最终登录确认
        if not login_success and not self.stop_flag:
            try:
                final_state = self.check_login_state(page)
                if final_state.get('isLoggedIn', False):
                    login_success = True
                    self.log("[登录] ✅ 最终检测到登录成功！")
            except Exception:
                pass

        # 6. 保存登录状态
        if login_success:
            try:
                page.context.storage_state(path=self.storage_state_path)
                self.log("[登录] 💾 登录状态已保存，下次可直接使用")
            except Exception as e:
                self.log(f"[登录] ⚠️ 保存登录状态失败: {e}")
        else:
            self.log("[登录] ❌ 登录超时，将尝试无登录模式")
            self.log("[登录] ⚠️ 部分功能可能受限")

        return login_success

    def capture_with_complete_login(self, items, screenshot_dir):
        """带完整登录的抓取功能"""
        results = []
        covers_dir = os.path.join(screenshot_dir, 'covers')
        os.makedirs(covers_dir, exist_ok=True)

        self.log("[浏览器] 启动完整登录版浏览器...")

        with sync_playwright() as p:
            try:
                os.makedirs(self.user_data_dir, exist_ok=True)
                context = p.chromium.launch_persistent_context(
                    user_data_dir=self.user_data_dir,
                    headless=False,
                    viewport={'width': 1920, 'height': 1080},
                    user_agent=self.http_user_agent,
                )
                self.log(f"[登录] 使用持久化用户目录: {self.user_data_dir}")
            except Exception as e:
                self.log(f"[错误] 无法启动浏览器: {e}")
                raise

            page = context.pages[0] if context.pages else context.new_page()
            page.set_default_timeout(60000)

            # 执行登录
            login_success = self.perform_login(page)

            # 处理链接
            for idx, item in enumerate(items, 1):
                if self.stop_flag:
                    self.log("[停止] 用户中断")
                    break

                link = item.get('链接', '')
                product = item.get('产品', '')
                seq_val = item.get('序号', str(idx))
                name_prefix = self.sanitize_name(f"{product}_{seq_val}")

                self.log(f"[{idx}/{len(items)}] 处理: {link[:60]}...")

                result = {
                    '序号': seq_val,
                    '产品': product,
                    '链接': link,
                    '笔记ID': self.extract_note_id(link),
                    '采集状态': '失败',
                    '错误信息': '',
                    'HTTP状态': '',
                    '截屏文件': '',
                    '封面图列表': [],
                    '检测时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    '登录状态': '成功' if login_success else '未登录'
                }

                try:
                    # 访问链接
                    self.log(f"  访问链接...")
                    resp = page.goto(link, timeout=45000, wait_until='domcontentloaded')
                    result['HTTP状态'] = resp.status if resp else ''
                    time.sleep(3)

                    # 检查登录弹窗
                    if not login_success:
                        has_login_popup = page.evaluate("""() => {
                            const modal = document.querySelector('.login-modal, [class*="LoginModal"]');
                            const qrCode = document.querySelector('[class*="qrcode"], [class*="QRCode"]');
                            return !!(modal || qrCode);
                        }""")

                        if has_login_popup:
                            self.log(f"  ⚠️ 检测到登录弹窗，跳过此链接")
                            result['错误信息'] = "需要登录但用户未完成登录"
                            results.append(result)
                            continue

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
                    self.log(f"  ✅ 处理完成")

                except Exception as e:
                    result['错误信息'] = str(e)
                    self.log(f"  ❌ 处理失败: {e}")

                results.append(result)

                # 链接间延迟
                if idx < len(items):
                    time.sleep(2)

            try:
                context.close()
            except Exception:
                pass
            self.log("[关闭] 浏览器已关闭")

        return results

    def run_complete_test(self):
        """运行完整登录测试"""
        print("="*80)
        print("小红书链接监控工具 - 完整登录版测试")
        print("="*80)

        # 1. 准备测试数据
        csv_file = "test_links_fixed.csv"
        if not os.path.exists(csv_file):
            try:
                df = pd.read_excel('link.xlsx')
                links = df['link'].tolist()[:2]  # 测试2个链接

                with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['产品', '序号', '链接'])
                    for i, link in enumerate(links, 1):
                        writer.writerow([f'登录测试{i}', str(i), link])

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
        output_dir = "complete_login_test_output"
        screenshot_dir = os.path.join(output_dir, 'screenshots')
        os.makedirs(screenshot_dir, exist_ok=True)

        self.log(f"📁 输出目录: {output_dir}")

        # 4. 开始测试
        try:
            self.log("="*60)
            self.log("🚀 开始完整登录版测试...")
            self.log("🔧 测试功能:")
            self.log("   1. 完整扫码登录流程")
            self.log("   2. 登录状态检测")
            self.log("   3. 持久化登录保存")
            self.log("   4. 链接内容抓取")
            self.log("="*60)

            # 运行完整登录测试
            results = self.capture_with_complete_login(items, screenshot_dir)

            # 5. 生成报告
            if results:
                self.log("="*60)
                self.log("✅ 完整登录版测试完成！")

                success_count = sum(1 for r in results if r.get('采集状态') == '成功')
                login_success = sum(1 for r in results if r.get('登录状态') == '成功')

                self.log(f"📊 总计: {len(results)} 条")
                self.log(f"✅ 成功: {success_count} 条")
                self.log(f"🔐 登录: {login_success} 条")
                self.log("="*60)

                # 保存结果
                with open(os.path.join(output_dir, 'complete_login_results.json'), 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)

                self.log(f"📄 结果已保存: complete_login_results.json")
                return True

        except KeyboardInterrupt:
            self.log("\n⚠️ 测试被用户中断")
            return False
        except Exception as e:
            self.log(f"❌ 测试失败: {e}")
            return False

if __name__ == "__main__":
    print("完整登录版测试工具启动...")

    monitor = CompleteLoginFixedMonitor()

    try:
        success = monitor.run_complete_test()
        if success:
            print("\n🎉 完整登录版测试成功！")
            print("请检查输出目录中的结果和截图")
        else:
            print("\n❌ 测试遇到问题")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")