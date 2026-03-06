#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版粉丝数提取测试程序
基于测试结果，直接从页面提取粉丝数信息
"""

import os
import time
from playwright.sync_api import sync_playwright
from datetime import datetime

class FansExtractor:
    def __init__(self):
        self.output_dir = "test_results"
        os.makedirs(self.output_dir, exist_ok=True)

    def log(self, message, level='info'):
        """简单日志输出"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        prefix = {
            'info': '[信息]',
            'success': '✅',
            'error': '❌',
            'warning': '⚠️',
            'debug': '[调试]'
        }.get(level, '[信息]')
        print(f"{timestamp} {prefix} {message}")

    def extract_fans_from_page(self, page, url):
        """从页面提取粉丝数信息"""
        try:
            self.log(f"开始访问页面: {url}")
            page.goto(url, wait_until='networkidle')
            time.sleep(3)

            # 基于测试结果，我们知道粉丝数信息直接显示在页面上
            fans_data = page.evaluate("""
                () => {
                    const result = {
                        fans: '',
                        confidence: 0,
                        method: '',
                        debug: []
                    };

                    // 1. 查找包含"粉丝"文本的所有元素
                    const elements = document.querySelectorAll('*');
                    const fansElements = [];

                    elements.forEach(el => {
                        const text = (el.innerText || el.textContent || '').trim();
                        if (text.includes('粉丝') || text.includes('关注者')) {
                            const rect = el.getBoundingClientRect();
                            if (rect.width > 0 && rect.height > 0 && el.offsetParent !== null) {
                                fansElements.push({
                                    element: el,
                                    text: text,
                                    rect: rect,
                                    className: (el.className || '').toString(),
                                    tagName: el.tagName
                                });
                            }
                        }
                    });

                    result.debug.push(`找到 ${fansElements.length} 个包含粉丝信息的元素`);

                    // 2. 按优先级解析粉丝数
                    // 优先级1: 查找用户信息区域（如 "26关注 5.1万粉丝 32.8万获赞与收藏"）
                    for (const el of fansElements) {
                        const text = el.text;
                        if (text.includes('关注') && text.includes('粉丝') && text.includes('获赞')) {
                            const fansMatch = text.match(/([0-9]+\.?[0-9]*[万wWkK]?)\s*粉丝/);
                            if (fansMatch) {
                                result.fans = fansMatch[1];
                                result.confidence = 95;
                                result.method = 'user_info_block';
                                result.debug.push(`从用户信息块提取: ${text}`);
                                return result;
                            }
                        }
                    }

                    // 优先级2: 直接匹配"数字+粉丝"格式
                    for (const el of fansElements) {
                        const text = el.text;
                        const patterns = [
                            /([0-9]+\.?[0-9]*[万wWkK]?)\s*粉丝/,
                            /粉丝[:\s：]*([0-9]+\.?[0-9]*[万wWkK]?)/,
                            /([0-9]+\.?[0-9]*[万wWkK]?)\s*(粉丝|关注者)/
                        ];

                        for (const pattern of patterns) {
                            const match = text.match(pattern);
                            if (match) {
                                const fansNumber = match[1] || match[2];
                                if (fansNumber) {
                                    result.fans = fansNumber;
                                    result.confidence = 90;
                                    result.method = 'direct_text_match';
                                    result.debug.push(`找到匹配: ${text}`);
                                    result.debug.push(`提取粉丝数: ${fansNumber}`);
                                    return result;
                                }
                            }
                        }
                    }

                    // 优先级3: 单独的粉丝数元素
                    for (const el of fansElements) {
                        const text = el.text.trim();
                        if (text.includes('粉丝') && text.length < 30) {
                            const fansMatch = text.match(/([0-9]+\.?[0-9]*[万wWkK]?)/);
                            if (fansMatch) {
                                result.fans = fansMatch[1];
                                result.confidence = 70;
                                result.method = 'fans_element_only';
                                result.debug.push(`从单独粉丝元素提取: ${text}`);
                                return result;
                            }
                        }
                    }

                    result.debug.push('所有解析方法均失败');
                    return result;
                }
            """)

            # 记录结果
            self.log(f"解析方法: {fans_data.get('method', 'none')}")
            self.log(f"置信度: {fans_data.get('confidence', 0)}%")

            # 显示调试信息
            for msg in fans_data.get('debug', []):
                self.log(f"调试: {msg}", 'debug')

            # 提取粉丝数
            if fans_data and fans_data.get('fans'):
                fans_number = fans_data['fans']
                method = fans_data.get('method', '')

                self.log(f"✅ 提取成功: {fans_number} (方法: {method})", 'success')
                return fans_number
            else:
                self.log("❌ 未能提取到粉丝数", 'error')
                return ""

        except Exception as e:
            self.log(f"提取失败: {str(e)}", 'error')
            return ""

    def test_single_url(self, url):
        """测试单个URL的粉丝数提取"""
        print(f"\n{'='*60}")
        print(f"测试URL: {url}")
        print(f"{'='*60}")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()

            try:
                # 保存初始截图
                page.screenshot(path=f"{self.output_dir}/initial_page.png")
                self.log("已保存初始页面截图")

                # 提取粉丝数
                fans_number = self.extract_fans_from_page(page, url)

                # 保存结果截图
                page.screenshot(path=f"{self.output_dir}/extraction_result.png")
                self.log("已保存结果截图")

                # 保存结果到文件
                result_file = os.path.join(self.output_dir, "extraction_result.txt")
                with open(result_file, 'w', encoding='utf-8') as f:
                    f.write(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n")
                    f.write(f"测试URL: {url}\\n")
                    f.write(f"提取结果: {fans_number}\\n")
                    f.write(f"状态: {'成功' if fans_number else '失败'}\\n")

                return fans_number

            except Exception as e:
                self.log(f"测试过程出错: {str(e)}", 'error')
                return ""
            finally:
                time.sleep(2)
                browser.close()

def main():
    """主函数"""
    extractor = FansExtractor()

    print("🚀 简化版粉丝数提取测试程序")
    print("基于之前的测试结果，直接从页面提取粉丝数信息")
    print()

    # 获取测试URL
    url = input("请输入小红书链接: ").strip()
    if not url:
        print("❌ 未提供链接")
        return

    # 执行测试
    result = extractor.test_single_url(url)

    print(f"\n{'='*60}")
    if result:
        print(f"🎉 测试成功！提取到粉丝数: {result}")
        print(f"📁 结果已保存到: {extractor.output_dir}/")
    else:
        print(f"❌ 测试失败，未能提取到粉丝数")
        print(f"📁 调试信息已保存到: {extractor.output_dir}/")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()