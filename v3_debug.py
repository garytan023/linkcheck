"""
WPP MD 小红书链接监测工具 - v3.0 调试版本
用于逐步诊断问题
"""

import tkinter as tk
from tkinter import ttk
import sys

print("调试开始...")
print("Python版本:", sys.version)

# 逐步检查依赖
try:
    print("正在导入tkinter...")
    import tkinter as tk
    print("✓ tkinter 导入成功")
except Exception as e:
    print("✗ tkinter 导入失败:", e)
    sys.exit(1)

try:
    print("正在导入ttk...")
    from tkinter import ttk
    print("✓ ttk 导入成功")
except Exception as e:
    print("✗ ttk 导入失败:", e)
    sys.exit(1)

try:
    print("正在导入csv...")
    import csv
    print("✓ csv 导入成功")
except Exception as e:
    print("✗ csv 导入失败:", e)
    sys.exit(1)

try:
    print("正在导入threading...")
    import threading
    print("✓ threading 导入成功")
except Exception as e:
    print("✗ threading 导入失败:", e)
    sys.exit(1)

try:
    print("正在导入random...")
    import random
    print("✓ random 导入成功")
except Exception as e:
    print("✗ random 导入失败:", e)
    sys.exit(1)

try:
    print("正在导入datetime...")
    from datetime import datetime
    print("✓ datetime 导入成功")
except Exception as e:
    print("✗ datetime 导入失败:", e)
    sys.exit(1)

# 尝试导入其他依赖
try:
    print("正在导入playwright...")
    from playwright.sync_api import sync_playwright
    print("✓ playwright 导入成功")
except Exception as e:
    print("✗ playwright 导入失败:", e)
    print("继续使用简化模式...")

try:
    print("正在导入PIL...")
    from PIL import Image
    print("✓ PIL 导入成功")
except Exception as e:
    print("✗ PIL 导入失败:", e)
    print("继续使用简化模式...")

try:
    print("正在导入openpyxl...")
    import openpyxl
    print("✓ openpyxl 导入成功")
except Exception as e:
    print("✗ openpyxl 导入失败:", e)
    print("继续使用简化模式...")

print("\n所有依赖检查完成，开始创建GUI...")

class DebugV3:
    def __init__(self, root):
        print("正在初始化DebugV3...")
        self.root = root
        self.root.title("WPP MD v3.0 调试版本")

        print("正在设置窗口属性...")
        try:
            self.root.geometry("600x400")
            self.root.configure(bg='#F8F9FA')
            print("✓ 窗口属性设置成功")
        except Exception as e:
            print("✗ 窗口属性设置失败:", e)
            raise

        print("正在创建主框架...")
        try:
            main_frame = tk.Frame(root, bg='#F8F9FA')
            main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
            print("✓ 主框架创建成功")
        except Exception as e:
            print("✗ 主框架创建失败:", e)
            raise

        print("正在创建标题标签...")
        try:
            title_label = tk.Label(main_frame, text="WPP MD v3.0 调试版本",
                                 font=('Arial', 16, 'bold'),
                                 bg='#F8F9FA', fg='#2D3748')
            title_label.pack(pady=20)
            print("✓ 标题标签创建成功")
        except Exception as e:
            print("✗ 标题标签创建失败:", e)
            raise

        print("正在创建状态标签...")
        try:
            self.status_label = tk.Label(main_frame, text="调试版本正在运行...",
                                      font=('Arial', 12),
                                      bg='#F8F9FA', fg='#34C759')
            self.status_label.pack(pady=10)
            print("✓ 状态标签创建成功")
        except Exception as e:
            print("✗ 状态标签创建失败:", e)
            raise

        print("正在创建测试按钮...")
        try:
            test_button = tk.Button(main_frame, text="测试功能",
                                  command=self.test_function,
                                  font=('Arial', 11),
                                  bg='#5B6FB5', fg='white',
                                  padx=20, pady=10)
            test_button.pack(pady=20)
            print("✓ 测试按钮创建成功")
        except Exception as e:
            print("✗ 测试按钮创建失败:", e)
            raise

        print("GUI创建完成！")

    def test_function(self):
        """测试功能"""
        print("测试按钮被点击！")
        self.status_label.config(text="测试功能正常！", fg='#34C759')
        self.root.after(2000, lambda: self.status_label.config(text="调试版本正在运行...", fg='#34C759'))

def main():
    print("main函数开始...")

    try:
        print("正在创建Tkinter根窗口...")
        root = tk.Tk()
        print("✓ 根窗口创建成功")
    except Exception as e:
        print("✗ 根窗口创建失败:", e)
        return

    try:
        print("正在创建应用实例...")
        app = DebugV3(root)
        print("✓ 应用实例创建成功")
    except Exception as e:
        print("✗ 应用实例创建失败:", e)
        import traceback
        traceback.print_exc()
        return

    try:
        print("正在启动主循环...")
        root.mainloop()
        print("✓ 主循环正常退出")
    except Exception as e:
        print("✗ 主循环异常:", e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("启动调试版本...")
    main()
    print("调试版本结束")