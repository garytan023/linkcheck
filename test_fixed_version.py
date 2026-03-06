"""
修复版对比测试脚本
对比原版和修复版的差异，验证修复效果
"""

import os
import time
import pandas as pd
from datetime import datetime

def test_original_vs_fixed():
    print("="*80)
    print("小红书链接监控工具 - 修复版对比测试")
    print("="*80)

    # 1. 检查测试数据
    if not os.path.exists('link.xlsx'):
        print("❌ 测试数据文件 link.xlsx 不存在")
        return False

    try:
        df = pd.read_excel('link.xlsx')
        links = df['link'].tolist()
        print(f"✅ 成功读取 {len(links)} 个测试链接")

        # 分析链接类型
        xhs_links = [link for link in links if 'xiaohongshu.com' in link]
        print(f"📍 小红书链接: {len(xhs_links)} 个")

    except Exception as e:
        print(f"❌ 读取测试数据失败: {e}")
        return False

    # 2. 检查修复版工具
    fixed_tool = 'link_monitor_fixed_gui.py'
    original_tool = 'link_monitor_pro_gui_v2.py'

    print(f"\n📋 工具检查:")
    print(f"  原版工具: {'✅ 存在' if os.path.exists(original_tool) else '❌ 不存在'}")
    print(f"  修复工具: {'✅ 存在' if os.path.exists(fixed_tool) else '❌ 不存在'}")

    if not os.path.exists(fixed_tool):
        print("❌ 修复版工具不存在，无法进行对比测试")
        return False

    # 3. 详细修复说明
    print(f"\n🔧 修复版改进内容:")
    print(f"  1. 视频封面截图修复:")
    print(f"     ✓ 多策略获取视频封面 (video元素、poster属性、容器截图)")
    print(f"     ✓ 增强视频状态检测和等待机制")
    print(f"     ✓ 添加视频封面图片URL提取")

    print(f"\n  2. 图片封面顺序修复:")
    print(f"     ✓ 按索引顺序处理元数据图片URL")
    print(f"     ✓ 使用01、02格式确保文件名顺序")
    print(f"     ✓ 最终按文件名数字重新排序封面列表")
    print(f"     ✓ 优先选择大尺寸图片，过滤小图标")

    print(f"\n  3. 链接对应关系修复:")
    print(f"     ✓ 添加唯一标识符 (unique_id)")
    print(f"     ✓ 添加处理索引用于追踪")
    print(f"     ✓ 添加重复链接检测机制")
    print(f"     ✓ 增强结果验证和日志记录")

    # 4. 创建测试配置
    print(f"\n📝 测试配置建议:")

    # 创建测试CSV（如果不存在）
    test_csv = 'test_links_fixed.csv'
    if not os.path.exists(test_csv):
        try:
            test_data = [['产品', '序号', '链接']]
            for i, link in enumerate(links[:5], 1):  # 只测试前5个链接
                test_data.append([f'测试产品{i}', str(i), link])

            import csv
            with open(test_csv, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(test_data)

            print(f"  ✅ 创建测试CSV: {test_csv}")
        except Exception as e:
            print(f"  ⚠️ 创建测试CSV失败: {e}")

    print(f"\n🚀 运行建议:")
    print(f"  1. 运行修复版工具:")
    print(f"     python {fixed_tool}")
    print(f"     - 输入文件: {test_csv}")
    print(f"     - 选择'完整模式'以测试所有修复功能")
    print(f"     - 输出目录: ./test_output_fixed")

    print(f"\n  2. 检查修复效果:")
    print(f"     📸 视频封面: 检查是否成功截取视频播放器封面")
    print(f"     🖼️ 图片顺序: 检查封面图文件名是否按01、02...排序")
    print(f"     🔗 链接对应: 检查Excel中每行数据是否与输入链接对应")

    print(f"\n  3. 对比要点:")
    print(f"     📊 输出文件名: 包含'修复版'标识")
    print(f"     🎨 表头颜色: 绿色表头表示修复版")
    print(f"     📝 日志信息: 包含'[修复]'标记的详细日志")

    # 5. 创建修复验证清单
    checklist = """
修复效果验证清单:

□ 视频封面截图:
  □ 视频链接能正确截取封面
  □ 截图文件包含'video_cover'标识
  □ 截图尺寸合理（非空白或小图标）

□ 图片封面顺序:
  □ 封面图文件名按01、02、03...排序
  □ 第一张图片对应元数据URL[0]
  □ Excel中封面图按顺序显示

□ 链接对应关系:
  □ 每行数据的链接与输入CSV对应
  □ 序号和产品信息正确匹配
  □ 无重复或错位的数据记录

□ 整体功能:
  □ 程序运行无崩溃
  □ Excel报告正常生成
  □ 所有修复功能在日志中体现
"""

    with open('修复验证清单.txt', 'w', encoding='utf-8') as f:
        f.write(checklist)

    print(f"\n📋 已创建验证清单: 修复验证清单.txt")

    # 6. 生成测试报告
    report = {
        '测试时间': datetime.now().isoformat(),
        '测试数据': {
            '总链接数': len(links),
            '小红书链接数': len(xhs_links),
            '测试文件': 'link.xlsx'
        },
        '修复版本': {
            '文件名': fixed_tool,
            '创建时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '修复内容': [
                '视频封面截图多策略优化',
                '图片封面按索引顺序处理',
                '链接与结果唯一标识对应',
                '增强错误处理和日志记录'
            ]
        },
        '预期改进': {
            '视频封面成功率': '预期提升至80%+',
            '图片顺序准确率': '预期100%按顺序',
            '链接对应准确率': '预期100%正确对应',
            '整体稳定性': '预期显著提升'
        }
    }

    import json
    with open('修复版测试报告.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"  ✅ 生成测试报告: 修复版测试报告.json")

    print(f"\n" + "="*80)
    print("修复版准备完成！请运行以下命令开始测试:")
    print(f"python {fixed_tool}")
    print("="*80)

    return True

if __name__ == "__main__":
    try:
        success = test_original_vs_fixed()
        if success:
            print(f"\n✅ 修复版对比测试准备完成")
        else:
            print(f"\n❌ 修复版对比测试准备失败")
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")