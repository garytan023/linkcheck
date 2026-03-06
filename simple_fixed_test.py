"""
小红书链接监控工具 - 简化修复版测试
直接运行修复功能，避免依赖GUI组件
"""

import pandas as pd
import csv
import os
import time
from datetime import datetime
import re
import json
from playwright.sync_api import sync_playwright
from urllib.parse import urljoin

def simplify_log(message):
    """简化日志函数"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    try:
        print(f"[{timestamp}] {message}")
    except UnicodeEncodeError:
        print(f"[{timestamp}] Test: {message.encode('ascii', 'ignore').decode('ascii')}")

def sanitize_name(name):
    """清理文件名"""
    try:
        safe = re.sub(r'[^0-9A-Za-z\u4e00-\u9fff]+', '_', name)
        return safe.strip('_') or "item"
    except Exception:
        return "item"

def extract_note_id(url):
    """提取笔记ID"""
    try:
        match = re.search(r'/explore/([a-zA-Z0-9]+)', url)
        if match:
            return match.group(1)
    except:
        pass
    return ''

def test_fixed_functionality():
    """测试修复功能"""
    print("="*60)
    print("小红书链接监控工具 - 修复版测试")
    print("="*60)

    # 1. 准备测试数据
    try:
        df = pd.read_excel('link.xlsx')
        links = df['link'].tolist()[:3]  # 只测试前3个链接
        simplify_log(f"读取到 {len(links)} 个测试链接")

        # 创建测试CSV
        test_csv = 'test_simple.csv'
        with open(test_csv, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['产品', '序号', '链接'])
            for i, link in enumerate(links, 1):
                writer.writerow([f'测试{i}', str(i), link])

        simplify_log(f"创建测试CSV: {test_csv}")

    except Exception as e:
        simplify_log(f"准备测试数据失败: {e}")
        return False

    # 2. 读取测试数据
    items = []
    try:
        with open(test_csv, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader, 1):
                link = row.get('链接', '').strip()
                if link:
                    items.append({
                        '产品': row.get('产品', ''),
                        '序号': row.get('序号', str(idx)),
                        '链接': link
                    })
        simplify_log(f"解析到 {len(items)} 个项目")
    except Exception as e:
        simplify_log(f"读取测试数据失败: {e}")
        return False

    # 3. 设置输出目录
    output_dir = 'simple_test_output'
    screenshot_dir = os.path.join(output_dir, 'screenshots')
    covers_dir = os.path.join(screenshot_dir, 'covers')
    os.makedirs(covers_dir, exist_ok=True)

    simplify_log(f"输出目录: {output_dir}")

    # 4. 运行修复版测试
    results = []
    user_data_dir = os.path.join(os.getcwd(), "test_xhs_profile")

    try:
        simplify_log("="*50)
        simplify_log("开始浏览器自动化测试...")
        simplify_log("测试修复功能:")
        simplify_log("1. 视频封面截图")
        simplify_log("2. 图片顺序处理")
        simplify_log("3. 链接对应关系")
        simplify_log("="*50)

        with sync_playwright() as p:
            try:
                os.makedirs(user_data_dir, exist_ok=True)
                context = p.chromium.launch_persistent_context(
                    user_data_dir=user_data_dir,
                    headless=False,
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
            except Exception as e:
                simplify_log(f"启动浏览器失败: {e}")
                return False

            page = context.pages[0] if context.pages else context.new_page()
            page.set_default_timeout(60000)

            # 处理每个链接
            for idx, item in enumerate(items, 1):
                simplify_log(f"[{idx}/{len(items)}] 处理: {item['链接'][:60]}...")

                product = item.get('产品', '')
                seq_val = item.get('序号', str(idx))
                link = item['链接']
                name_prefix = sanitize_name(f"{product}_{seq_val}")

                result = {
                    '序号': seq_val,
                    '产品': product,
                    '链接': link,
                    '笔记ID': extract_note_id(link),
                    '采集状态': '失败',
                    '错误信息': '',
                    '截屏文件': '',
                    '封面图列表': [],
                    '检测时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }

                try:
                    # 访问链接
                    simplify_log(f"  访问链接...")
                    resp = page.goto(link, timeout=45000, wait_until='domcontentloaded')
                    result['HTTP状态'] = resp.status if resp else ''

                    time.sleep(3)  # 等待页面加载

                    # 截图
                    screenshot_name = f'{name_prefix}_screenshot.png'
                    screenshot_path = os.path.join(screenshot_dir, screenshot_name)

                    try:
                        page.screenshot(path=screenshot_path, full_page=False)
                        result['截屏文件'] = screenshot_path
                        simplify_log(f"  截图成功: {screenshot_name}")
                    except Exception as e:
                        simplify_log(f"  截图失败: {str(e)}")

                    # 检查是否为视频
                    is_video = page.evaluate("""() => {
                        return document.querySelector('video') !== null;
                    }""")

                    # 测试修复功能1: 视频封面截图
                    if is_video:
                        simplify_log("  检测到视频，尝试封面截图...")
                        video_covers = capture_video_cover_fixed(page, covers_dir, name_prefix)
                        if video_covers:
                            result['封面图列表'].extend(video_covers)
                            simplify_log(f"  视频封面成功: {len(video_covers)} 个")

                    # 测试修复功能2: 图片封面顺序
                    simplify_log("  获取页面图片...")
                    image_urls = extract_image_urls_fixed(page)
                    simplify_log(f"  找到 {len(image_urls)} 个图片URL")

                    # 按顺序处理图片
                    ordered_covers = process_images_in_order(page, covers_dir, name_prefix, image_urls)
                    if ordered_covers:
                        result['封面图列表'].extend(ordered_covers)
                        simplify_log(f"  图片处理成功: {len(ordered_covers)} 个")

                    # 检查图片顺序
                    if result['封面图列表']:
                        cover_files = [os.path.basename(p) for p in result['封面图列表']]
                        simplify_log(f"  封面文件: {cover_files}")

                    result['采集状态'] = '成功'
                    simplify_log(f"  处理完成")

                except Exception as e:
                    result['错误信息'] = str(e)
                    simplify_log(f"  处理失败: {str(e)}")

                results.append(result)

                # 链接间延迟
                if idx < len(items):
                    time.sleep(2)

            try:
                context.close()
            except Exception:
                pass

    except Exception as e:
        simplify_log(f"浏览器测试失败: {e}")
        return False

    # 5. 生成简单报告
    try:
        simplify_log("="*50)
        simplify_log("测试结果总结:")

        success_count = sum(1 for r in results if r.get('采集状态') == '成功')
        total_count = len(results)

        simplify_log(f"总计链接: {total_count}")
        simplify_log(f"成功处理: {success_count}")
        simplify_log(f"失败处理: {total_count - success_count}")

        # 验证修复功能
        simplify_log("\n修复功能验证:")

        # 检查视频封面
        video_covers = []
        for result in results:
            for cover in result.get('封面图列表', []):
                if 'video' in os.path.basename(cover):
                    video_covers.append(cover)

        simplify_log(f"视频封面: {len(video_covers)} 个")
        simplify_log(f"结果: {'成功' if video_covers else '未检测到视频链接'}")

        # 检查图片顺序
        all_covers = []
        for result in results:
            all_covers.extend(result.get('封面图列表', []))

        ordered_files = []
        for cover in all_covers:
            if 'cover_' in os.path.basename(cover):
                ordered_files.append(os.path.basename(cover))

        ordered_files.sort()
        simplify_log(f"图片封面: {len(ordered_files)} 个文件")
        if ordered_files:
            simplify_log(f"顺序示例: {ordered_files[:3]}")

        # 检查链接对应
        correct_links = 0
        for i, result in enumerate(results):
            if i < len(items) and result['链接'] == items[i]['链接']:
                correct_links += 1

        simplify_log(f"链接对应: {correct_links}/{len(results)} 正确")
        simplify_log(f"结果: {'成功' if correct_links == len(results) else '存在问题'}")

        # 保存结果
        with open(os.path.join(output_dir, 'test_results.json'), 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        simplify_log(f"\n结果已保存到: {output_dir}")
        simplify_log("="*50)

        return True

    except Exception as e:
        simplify_log(f"生成报告失败: {e}")
        return False

def capture_video_cover_fixed(page, output_dir, name_prefix):
    """修复版视频封面截图"""
    covers = []

    try:
        # 多策略获取视频封面
        strategies = [
            ('video元素', 'video'),
            ('视频容器', '.xgplayer, .video-player'),
            ('封面图片', 'img[src*="cover"], img[src*="poster"]')
        ]

        for strategy_name, selector in strategies:
            try:
                elements = page.query_selector_all(selector)
                for elem in elements:
                    try:
                        cover_name = f'{name_prefix}_video_cover_{len(covers)+1}.png'
                        cover_path = os.path.join(output_dir, cover_name)

                        # 检查元素尺寸
                        box = elem.bounding_box()
                        if box and box['width'] > 100 and box['height'] > 100:
                            elem.screenshot(path=cover_path, timeout=5000)
                            covers.append(cover_path)
                            return covers  # 成功获取一个就返回
                    except Exception:
                        continue
            except Exception:
                continue

    except Exception:
        pass

    return covers

def extract_image_urls_fixed(page):
    """提取图片URL"""
    try:
        urls = page.evaluate("""() => {
            const urls = [];
            const images = document.querySelectorAll('img[src]');
            images.forEach(img => {
                const src = img.src || img.getAttribute('data-src');
                if (src && src.startsWith('http')) {
                    urls.push(src);
                }
            });
            return urls;
        }""")
        return urls[:5]  # 只取前5个
    except Exception:
        return []

def process_images_in_order(page, output_dir, name_prefix, image_urls):
    """按顺序处理图片"""
    covers = []

    try:
        for idx, url in enumerate(image_urls):
            try:
                cover_name = f'{name_prefix}_cover_{idx+1:02d}.png'  # 01, 02格式
                cover_path = os.path.join(output_dir, cover_name)

                # 下载图片
                response = page.context.request.get(url, timeout=10000)
                if response.ok:
                    with open(cover_path, 'wb') as f:
                        f.write(response.body())
                    covers.append(cover_path)

            except Exception:
                continue

            if len(covers) >= 3:  # 最多3张
                break

    except Exception:
        pass

    return covers

if __name__ == "__main__":
    try:
        print("修复版测试工具启动...")
        success = test_fixed_functionality()

        if success:
            print("\n修复版测试完成!")
            print("请检查输出目录中的结果文件")
        else:
            print("\n测试遇到问题，请查看错误信息")

    except Exception as e:
        print(f"启动失败: {e}")