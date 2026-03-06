#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
粉丝数悬停测试脚本
专门用于测试Playwright悬停功能
"""

import os
import time
from playwright.sync_api import sync_playwright

def test_hover_functionality():
    """测试悬停功能"""
    print("🚀 开始测试粉丝数悬停功能")
    print("="*50)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = context.new_page()

        try:
            # 导航到小红书链接（请替换为实际链接）
            test_url = input("请输入小红书链接: ").strip()
            if not test_url:
                print("❌ 未提供链接")
                return

            print(f"📍 正在访问: {test_url}")
            page.goto(test_url, wait_until='networkidle')
            time.sleep(3)

            # 创建调试目录
            debug_dir = "test_debug"
            os.makedirs(debug_dir, exist_ok=True)

            print("\n🔍 第1步：页面加载完成截图")
            page.screenshot(path=f"{debug_dir}/step1_loaded.png")
            print("✅ 保存: step1_loaded.png")

            # 添加视觉标记
            print("\n🎯 第2步：添加视觉标记")
            page.evaluate("""
                () => {
                    // 添加十字光标
                    const cursor = document.createElement('div');
                    cursor.id = 'test_cursor';
                    cursor.style.position = 'fixed';
                    cursor.style.width = '20px';
                    cursor.style.height = '20px';
                    cursor.style.border = '2px solid red';
                    cursor.style.borderRadius = '50%';
                    cursor.style.backgroundColor = 'rgba(255, 0, 0, 0.3)';
                    cursor.style.zIndex = '99999';
                    cursor.style.pointerEvents = 'none';
                    cursor.style.transform = 'translate(-50%, -50%)';
                    document.body.appendChild(cursor);

                    // 监听鼠标移动
                    document.addEventListener('mousemove', (e) => {
                        const cursor = document.getElementById('test_cursor');
                        if (cursor) {
                            cursor.style.left = e.clientX + 'px';
                            cursor.style.top = e.clientY + 'px';
                        }
                    });

                    // 查找用户头像元素 - 修复className处理
                    const elements = document.querySelectorAll('*');
                    const userElements = [];
                    elements.forEach((el, index) => {
                        const rect = el.getBoundingClientRect();
                        const text = (el.innerText || '').toLowerCase();
                        const className = (el.className || '').toString().toLowerCase();
                        if (rect.width > 30 && rect.height > 30 && rect.width < 150 && rect.height < 150) {
                            if (text.includes('头像') || className.includes('avatar') ||
                                className.includes('user') || className.includes('author')) {
                                userElements.push({
                                    element: el,
                                    rect: rect,
                                    className: className,
                                    tagName: el.tagName
                                });
                            }
                        }
                    });
                    return userElements;
                }
            """)

            print("✅ 已添加红色十字光标")

            # 标记找到的用户元素
            print("\n🔍 第3步：标记用户相关元素")
            user_elements = page.evaluate("""
                () => {
                    const elements = document.querySelectorAll('*');
                    let count = 0;
                    elements.forEach((el, index) => {
                        const rect = el.getBoundingClientRect();
                        if (rect.width > 10 && rect.height > 10) {
                            const text = (el.innerText || el.textContent || '').substring(0, 20);
                            const className = (el.className || '').toString().toLowerCase();
                            if (text.includes('用户') || text.includes('作者') ||
                                className.includes('user') || className.includes('author') ||
                                el.tagName === 'IMG') {
                                if (count < 10) {
                                    const marker = document.createElement('div');
                                    marker.style.position = 'fixed';
                                    marker.style.left = (rect.left + rect.width/2 - 15) + 'px';
                                    marker.style.top = (rect.top + rect.height/2 - 15) + 'px';
                                    marker.style.width = '30px';
                                    marker.style.height = '30px';
                                    marker.style.border = '2px solid blue';
                                    marker.style.borderRadius = '50%';
                                    marker.style.backgroundColor = 'rgba(0, 0, 255, 0.2)';
                                    marker.style.zIndex = '10000';
                                    marker.style.pointerEvents = 'none';
                                    marker.style.fontSize = '12px';
                                    marker.style.textAlign = 'center';
                                    marker.style.lineHeight = '30px';
                                    marker.style.color = 'blue';
                                    marker.style.fontWeight = 'bold';
                                    marker.innerHTML = (count + 1).toString();
                                    document.body.appendChild(marker);
                                    count++;
                                }
                            }
                        }
                    });
                    return count;
                }
            """)

            print(f"✅ 标记了 {user_elements} 个候选元素")
            page.screenshot(path=f"{debug_dir}/step2_marked.png")
            print("✅ 保存: step2_marked.png")

            print("\n🖱️ 第4步：自动测试悬停")
            for i in range(min(5, user_elements)):  # 测试前5个元素
                print(f"\n测试悬停元素 {i + 1}...")

                # 移动鼠标到指定位置
                target_x = 200 + (i * 100)
                target_y = 200 + (i * 50)

                page.mouse.move(target_x, target_y)
                time.sleep(1)

                print(f"  鼠标移动到: ({target_x}, {target_y})")
                page.screenshot(path=f"{debug_dir}/hover_test_{i+1}.png")
                print(f"  保存: hover_test_{i+1}.png")

                # 检查是否有弹出元素
                popup_count = page.evaluate("""
                    () => {
                        const elements = document.querySelectorAll('*');
                        let popupCount = 0;
                        elements.forEach(el => {
                            const style = window.getComputedStyle(el);
                            const rect = el.getBoundingClientRect();
                            const text = el.innerText || '';
                            if ((style.position === 'fixed' || style.position === 'absolute') &&
                                rect.width > 0 && rect.height > 0 &&
                                text.includes('粉丝') && el.style.zIndex > 1000) {
                                popupCount++;
                            }
                        });
                        return popupCount;
                    }
                """)

                if popup_count > 0:
                    print(f"  🎉 发现 {popup_count} 个粉丝相关弹出元素!")
                    page.screenshot(path=f"{debug_dir}/success_popup.png")
                    print("  ✅ 保存: success_popup.png")
                    break
                else:
                    print(f"  ❌ 未发现粉丝相关弹出元素")

            # 手动测试功能
            print("\n🎯 第5步：手动测试模式")
            print("📍 现在你可以手动移动鼠标来测试悬停效果")
            print("📝 移动鼠标到用户头像上，看看是否显示粉丝数")
            print("⏱️  程序将等待30秒，让你有足够时间手动测试")

            # 高亮显示所有可能的用户交互区域
            page.evaluate("""
                () => {
                    const elements = document.querySelectorAll('*');
                    let highlightCount = 0;
                    elements.forEach((el, index) => {
                        const rect = el.getBoundingClientRect();
                        const text = (el.innerText || '').toLowerCase();
                        const className = (el.className || '').toString().toLowerCase();
                        const style = window.getComputedStyle(el);

                        // 高亮所有可能的交互元素
                        if (rect.width > 10 && rect.height > 10 &&
                            (text.includes('用户') || text.includes('头像') || text.includes('作者') ||
                             className.includes('user') || className.includes('avatar') || className.includes('author') ||
                             className.includes('profile') || className.includes('card') ||
                             el.tagName === 'IMG' || style.cursor === 'pointer' ||
                             el.onclick || el.onmouseover)) {

                            if (highlightCount < 15) {
                                const highlight = document.createElement('div');
                                highlight.style.position = 'fixed';
                                highlight.style.left = (rect.left - 2) + 'px';
                                highlight.style.top = (rect.top - 2) + 'px';
                                highlight.style.width = (rect.width + 4) + 'px';
                                highlight.style.height = (rect.height + 4) + 'px';
                                highlight.style.border = '2px solid yellow';
                                highlight.style.backgroundColor = 'rgba(255, 255, 0, 0.2)';
                                highlight.style.zIndex = '9999';
                                highlight.style.pointerEvents = 'none';
                                highlight.innerHTML = highlightCount + 1;
                                highlight.style.fontSize = '10px';
                                highlight.style.color = 'black';
                                highlight.style.fontWeight = 'bold';
                                highlight.style.display = 'flex';
                                highlight.style.alignItems = 'center';
                                highlight.style.justifyContent = 'center';
                                document.body.appendChild(highlight);
                                highlightCount++;
                            }
                        }
                    });
                    return highlightCount;
                }
            """)

            print("✅ 已高亮显示所有可能的交互区域（黄色框）")
            page.screenshot(path=f"{debug_dir}/manual_test_start.png")
            print("✅ 保存: manual_test_start.png")

            # 添加实时检测功能
            print("🔍 开始实时检测粉丝数弹出...")
            for second in range(30):
                time.sleep(1)

                # 每隔几秒检测一次
                if second % 3 == 0:
                    fan_popups = page.evaluate("""
                        () => {
                            const elements = document.querySelectorAll('*');
                            const popups = [];
                            elements.forEach(el => {
                                const text = (el.innerText || '').toLowerCase();
                                const style = window.getComputedStyle(el);
                                const rect = el.getBoundingClientRect();

                                if (text.includes('粉丝') && rect.width > 0 && rect.height > 0) {
                                    popups.push({
                                        text: el.innerText.substring(0, 50),
                                        visible: el.offsetParent !== null,
                                        position: style.position,
                                        zIndex: style.zIndex,
                                        rect: [rect.left, rect.top, rect.width, rect.height]
                                    });
                                }
                            });
                            return popups;
                        }
                    """)

                    if fan_popups:
                        print(f"🎉 第{second}秒: 发现 {len(fan_popups)} 个粉丝相关元素!")
                        for i, popup in enumerate(fan_popups):
                            print(f"   元素{i+1}: {popup['text']} (可见: {popup['visible']}, 位置: {popup['rect']})")

                        # 立即截图
                        page.screenshot(path=f"{debug_dir}/manual_success.png")
                        print(f"✅ 保存截图: manual_success.png")

                        # 停止等待，退出循环
                        break
                    else:
                        if second % 5 == 0:  # 每5秒显示一次进度
                            print(f"⏱️  等待中... ({second}/30秒)")

                # 检测鼠标位置
                mouse_pos = page.evaluate("""
                    () => {
                        return {
                            x: window.lastMouseX || 0,
                            y: window.lastMouseY || 0
                        };
                    }
                """)

                # 更新鼠标追踪
                page.evaluate("""
                    () => {
                        document.addEventListener('mousemove', (e) => {
                            window.lastMouseX = e.clientX;
                            window.lastMouseY = e.clientY;
                        });
                    }
                """)

            # 手动测试结束，开始最终分析
            print("\n🔍 第6步：查找所有包含粉丝文本的元素")
            fans_elements = page.evaluate("""
                () => {
                    const elements = document.querySelectorAll('*');
                    const fansElements = [];
                    elements.forEach(el => {
                        const text = (el.innerText || el.textContent || '').toLowerCase();
                        if (text.includes('粉丝') || text.includes('关注者')) {
                            const rect = el.getBoundingClientRect();
                            if (rect.width > 0 && rect.height > 0) {
                                fansElements.push({
                                    text: text.substring(0, 50),
                                    visible: el.offsetParent !== null,
                                    rect: rect.toString(),
                                    className: (el.className || '').toString()
                                });
                            }
                        }
                    });
                    return fansElements;
                }
            """)

            print(f"📊 找到 {len(fans_elements)} 个粉丝相关元素:")
            for i, elem in enumerate(fans_elements):
                print(f"  {i+1}. {elem['text']} (可见: {elem['visible']})")

            print("\n✅ 测试完成!")
            print(f"📁 所有截图已保存到: {debug_dir}/")

        except Exception as e:
            print(f"❌ 测试过程中出错: {str(e)}")
            import traceback
            traceback.print_exc()

        finally:
            time.sleep(5)
            browser.close()

if __name__ == "__main__":
    test_hover_functionality()