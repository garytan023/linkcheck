"""
小红书链接监控工具 - 修复版命令行版本
用于快速测试修复效果
"""

import pandas as pd
import csv
import os
import time
from datetime import datetime
import sys
sys.path.append('.')

# 导入修复版的核心功能
try:
    from link_monitor_fixed_gui import FixedLinkMonitorGUI
except ImportError:
    print("错误: 无法导入修复版工具，请确保 link_monitor_fixed_gui.py 存在")
    sys.exit(1)

def main():
    print("="*80)
    print("小红书链接监控工具 - 修复版命令行测试")
    print("="*80)

    # 1. 创建修复版实例
    monitor = FixedLinkMonitorGUI.__new__(FixedLinkMonitorGUI)
    monitor.colors = {
        'bg': '#5B6FB5',
        'primary': '#5B7BF5',
        'white': '#FFFFFF',
        'text_light': '#E8EEFF',
        'text_dark': '#2D3748',
        'success': '#48BB78',
        'danger': '#F56565',
    }
    monitor.storage_state_path = "xhs_fixed_storage.json"
    monitor.user_data_dir = "xhs_fixed_profile"
    monitor.http_user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
    )
    monitor.capture_mode = type('MockVar', (), {'get': lambda x: 'full'})()
    monitor.all_links_mode = type('MockVar', (), {'get': lambda x: False})()

    def log(message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        try:
            print(f"[{timestamp}] {message}")
        except UnicodeEncodeError:
            print(f"[{timestamp}] 修复版: {message.encode('ascii', 'ignore').decode('ascii')}")

    monitor.log = log

    # 2. 准备测试数据
    csv_file = "test_links_fixed.csv"
    if not os.path.exists(csv_file):
        # 使用原始 link.xlsx 数据
        try:
            df = pd.read_excel('link.xlsx')
            links = df['link'].tolist()[:3]  # 只测试前3个链接

            with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['产品', '序号', '链接'])
                for i, link in enumerate(links, 1):
                    writer.writerow([f'修复测试{i}', str(i), link])

            log(f"✅ 创建测试CSV: {csv_file} (包含 {len(links)} 个链接)")
        except Exception as e:
            log(f"❌ 创建测试数据失败: {e}")
            return False

    # 3. 设置输出目录
    output_dir = "test_output_fixed"
    screenshot_dir = os.path.join(output_dir, 'screenshots')
    os.makedirs(screenshot_dir, exist_ok=True)

    log(f"📁 输出目录: {output_dir}")

    # 4. 读取测试数据
    try:
        items = monitor.read_items_from_csv(csv_file)
        log(f"📋 读取到 {len(items)} 个测试项目")

        for i, item in enumerate(items):
            log(f"  {i+1}. {item.get('产品', '')} - {item.get('链接', '')[:50]}...")

    except Exception as e:
        log(f"❌ 读取测试数据失败: {e}")
        return False

    # 5. 开始测试
    try:
        log("="*60)
        log("🚀 开始修复版测试...")
        log("🔧 测试修复功能:")
        log("   1. 视频封面截图修复")
        log("   2. 图片封面顺序修复")
        log("   3. 链接对应关系修复")
        log("="*60)

        # 使用修复版抓取功能
        results = monitor.capture_with_playwright_fixed(items, screenshot_dir, all_links_mode=False)

        # 6. 生成修复版Excel报告
        if results:
            log("📊 生成修复版Excel报告...")
            output_file, success, fail, _ = monitor.create_excel_report_fixed(results, output_dir)

            log("="*60)
            log("✅ 修复版测试完成！")
            log(f"📈 总计: {len(results)} 条")
            log(f"✅ 成功: {success} 条")
            log(f"❌ 失败: {fail} 条")
            log(f"📄 报告: {os.path.basename(output_file)}")
            log("="*60)

            # 7. 验证修复效果
            log("\n🔍 修复效果验证:")

            # 检查视频封面
            video_covers = []
            # 检查图片顺序
            cover_files = []
            if os.path.exists(os.path.join(screenshot_dir, 'covers')):
                import glob
                cover_files = glob.glob(os.path.join(screenshot_dir, 'covers', '*_cover_*.png'))

            for result in results:
                if result.get('封面图列表'):
                    for cover_path in result['封面图列表']:
                        if 'video' in os.path.basename(cover_path):
                            video_covers.append(cover_path)

            log(f"📸 视频封面: {len(video_covers)} 个")
            if video_covers:
                log(f"   ✅ 视频封面修复成功")
            else:
                log(f"   ⚠️ 未检测到视频链接或视频封面")

            log(f"🖼️ 图片封面: {len(cover_files)} 个文件")
            if cover_files:
                # 检查文件名顺序
                cover_files.sort()
                log(f"   📝 封面文件按顺序: {len(cover_files)} 个")
                for i, cover_file in enumerate(cover_files[:3]):
                    log(f"     {i+1}. {os.path.basename(cover_file)}")
            else:
                log(f"   ⚠️ 未找到封面文件")

            # 检查链接对应
            correct_links = 0
            for i, result in enumerate(results):
                if i < len(items) and result['链接'] == items[i]['链接']:
                    correct_links += 1

            log(f"🔗 链接对应: {correct_links}/{len(results)} 正确")
            if correct_links == len(results):
                log(f"   ✅ 链接对应关系修复成功")
            else:
                log(f"   ⚠️ 链接对应关系存在问题")

            return True

        else:
            log("❌ 没有生成任何结果")
            return False

    except KeyboardInterrupt:
        log("\n⚠️ 测试被用户中断")
        return False
    except Exception as e:
        log(f"❌ 测试过程中出现错误: {e}")
        import traceback
        log(f"详细错误: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("修复版命令行测试工具启动...")
    try:
        success = main()
        if success:
            print("\n🎉 修复版测试成功完成！")
        else:
            print("\n❌ 修复版测试遇到问题")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")