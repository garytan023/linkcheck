"""
v3.0 修复版本快速测试
"""

import sys
sys.path.append('.')

def test_v3_fixed():
    try:
        print("测试1: 导入模块")
        from v3_fixed_gui import UltimateMonitorV3Fixed
        print("PASS - 模块导入成功")

        print("测试2: 创建GUI实例")
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()  # 隐藏窗口
        app = UltimateMonitorV3Fixed(root)
        print("PASS - GUI实例创建成功")

        print("测试3: 测试update_stats函数")
        app.stats = {
            'total_processed': 10,
            'success_count': 8,
            'failed_count': 2,
            'anti_crawler_count': 1
        }
        app.update_stats()
        print("PASS - update_stats函数正常")

        print("测试4: 测试CSV读取")
        app.csv_file.set("v3_test_links.csv")
        items = app.read_links_from_csv(app.csv_file.get())
        print(f"PASS - 读取到 {len(items)} 个链接")

        root.destroy()
        print("所有测试通过！修复版本可以正常使用")
        return True

    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_v3_fixed()