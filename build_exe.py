"""
构建EXE文件脚本
用于将链接监测工具打包成独立的可执行文件
"""

import os
import subprocess
import sys
from datetime import datetime

# 设置输出编码为UTF-8
sys.stdout.reconfigure(encoding='utf-8')

def build_exe():
    """打包EXE文件"""
    
    print("="*60)
    print("WPP MD 小红书链接监测工具 - EXE打包程序")
    print("="*60)
    print()
    
    # 打包参数
    script_name = "link_monitor_pro_gui.py"
    exe_name = "WPP_MD_链接监测工具_Pro"
    browsers_dir = "browsers"  # 打包内置的Playwright浏览器目录
    
    print(f"[目标] 文件: {script_name}")
    print(f"[输出] 名称: {exe_name}.exe")
    print()
    
    # 检查源文件是否存在
    if not os.path.exists(script_name):
        print(f"[错误] 找不到源文件 {script_name}")
        return False
    
    print("[配置] 设置打包参数...")
    
    # 确保Playwright浏览器下载到本地目录（便于打包后免安装）
    try:
        os.makedirs(browsers_dir, exist_ok=True)
        print(f"[浏览器] 检查/下载 Chromium 到 {browsers_dir} ...")
        subprocess.run(
            ['py', '-3', '-m', 'playwright', 'install', 'chromium'],
            check=True,
            env={**os.environ, 'PLAYWRIGHT_BROWSERS_PATH': os.path.abspath(browsers_dir)}
        )
        print("[浏览器] 已就绪（打包后无需再装浏览器）")
    except Exception as e:
        print(f"[警告] 浏览器下载失败，打包后可能需要手动执行 playwright install chromium: {e}")

    # PyInstaller命令
    cmd = [
        'py', '-3', '-m', 'PyInstaller',
        '--name=' + exe_name,
        '--onefile',                    # 打包成单个exe文件
        '--windowed',                   # 不显示控制台窗口（GUI模式）
        '--noconfirm',                  # 覆盖已存在的文件不提示
        '--distpath=dist',              # 输出目录
        '--workpath=build_pro',         # 临时构建目录（避免权限冲突）
        '--add-data=yilideeplink.csv;.',  # 包含示例CSV文件
        '--add-data=' + f'{browsers_dir};browsers',  # 打包浏览器目录
        '--hidden-import=openpyxl',     # 确保包含openpyxl
        '--hidden-import=PIL',          # 确保包含PIL
        '--hidden-import=playwright',   # 确保包含playwright
        '--hidden-import=tkinter',      # 确保包含tkinter
        '--collect-all=playwright',     # 收集playwright所有文件
        script_name
    ]
    
    print("[开始] 正在打包...")
    print(f"   命令: {' '.join(cmd)}")
    print()
    print("[等待] 这可能需要几分钟时间，请耐心等待...")
    print()
    
    try:
        # 执行打包
        result = subprocess.run(cmd, check=True, capture_output=False, text=True)
        
        print()
        print("="*60)
        print("[成功] 打包完成！")
        print("="*60)
        print()
        print("[输出] 位置:")
        print(f"   dist/{exe_name}.exe")
        print()
        print("[文件] 大小:")
        exe_path = os.path.join('dist', f'{exe_name}.exe')
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"   {size_mb:.2f} MB")
        print()
        print("[使用] 说明:")
        print("   1. 进入 dist 目录")
        print(f"   2. 双击运行 {exe_name}.exe")
        print("   3. 将需要的CSV文件放在exe同一目录下")
        print()
        print("[提示] 已内置Playwright浏览器与Python运行时，无需额外安装。")
        print()
        
        return True
        
    except subprocess.CalledProcessError as e:
        print()
        print("="*60)
        print("[失败] 打包失败")
        print("="*60)
        print(f"错误: {e}")
        return False
    except Exception as e:
        print()
        print("="*60)
        print("[错误] 发生错误")
        print("="*60)
        print(f"错误: {e}")
        return False

if __name__ == '__main__':
    success = build_exe()
    
    if success:
        print("[完成] 全部完成！")
    else:
        print("[失败] 构建失败，请检查错误信息")
        sys.exit(1)
