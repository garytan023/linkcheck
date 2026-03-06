"""
构建 Ultimate v4 版本 EXE 的脚本。
会将 link_monitor_ultimate_v4.py 打包成独立 EXE，并把 Playwright 浏览器一并打包。
"""

import os
import subprocess
import sys
from datetime import datetime


def run_command(cmd, env=None):
    """执行命令并将命令打印出来，方便排查。"""
    print(f"[命令] {' '.join(cmd)}")
    subprocess.run(cmd, check=True, env=env)


def ensure_playwright_browsers(browsers_dir):
    """确保 Playwright Chromium 已经下载到指定目录。"""
    print(f"[浏览器] 检查/下载 Chromium 到 {browsers_dir} ...")
    env = os.environ.copy()
    env['PLAYWRIGHT_BROWSERS_PATH'] = os.path.abspath(browsers_dir)
    os.makedirs(browsers_dir, exist_ok=True)
    run_command(
        [sys.executable, '-m', 'playwright', 'install', 'chromium'],
        env=env,
    )
    print("[浏览器] 已就绪（打包后不会再去下载）")


def build_exe():
    script_name = "link_monitor_ultimate_v4.py"
    exe_name = "WPP_MD_链接监测工具_Ultimate_v4"
    dist_dir = "dist"
    build_dir = "build_ultimate_v4"
    browsers_dir = "browsers"
    csv_sample = "yilideeplink.csv"

    print("=" * 60)
    print("WPP MD 小红书链接监测工具 v4.0 Ultimate - EXE打包程序")
    print("=" * 60)
    print()

    if not os.path.exists(script_name):
        print(f"[错误] 找不到源文件 {script_name}")
        return False

    if not os.path.exists(csv_sample):
        print(f"[警告] 未找到示例 CSV 文件 {csv_sample}，将跳过内置。")

    try:
        ensure_playwright_browsers(browsers_dir)
    except Exception as exc:
        print(f"[警告] 浏览器准备失败: {exc}")
        print("       打包成功后可能需要用户手动执行 playwright install chromium")

    add_data_args = []
    if os.path.exists(csv_sample):
        add_data_args.append(f"--add-data={csv_sample}{os.pathsep}.")
    if os.path.isdir(browsers_dir):
        add_data_args.append(f"--add-data={browsers_dir}{os.pathsep}browsers")

    cmd = [
        sys.executable, '-m', 'PyInstaller',
        f'--name={exe_name}',
        '--onefile',
        '--windowed',
        '--noconfirm',
        f'--distpath={dist_dir}',
        f'--workpath={build_dir}',
        '--hidden-import=openpyxl',
        '--hidden-import=PIL',
        '--hidden-import=playwright',
        '--hidden-import=tkinter',
        '--hidden-import=requests',
        '--collect-all=playwright',
        '--collect-all=openpyxl',
        '--collect-all=PIL',
        *add_data_args,
        script_name,
    ]

    print("[开始] 正在打包...")
    print("[提示] 这一步会花几分钟时间。")
    print()

    run_command(cmd)

    exe_path = os.path.join(dist_dir, f"{exe_name}.exe")
    size_mb = os.path.getsize(exe_path) / (1024 * 1024) if os.path.exists(exe_path) else None
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print()
    print("=" * 60)
    print("[成功] Ultimate v4 打包完成")
    print("=" * 60)
    print(f"[时间] {timestamp}")
    print(f"[输出] {exe_path}")
    if size_mb:
        print(f"[大小] {size_mb:.2f} MB")
    print()
    print("[使用提示]")
    print(" 1. dist 目录下的 EXE 已内置 Playwright 浏览器")
    print(" 2. 将需要的 CSV（如 yilideeplink.csv）与 EXE 放在一起后直接双击运行")
    print(" 3. 如需飞书同步，请确保 feishu_config.json 与 EXE 同目录")
    print()
    return True


if __name__ == "__main__":
    try:
        build_exe()
    except subprocess.CalledProcessError as err:
        print()
        print("=" * 60)
        print("[失败] 打包失败")
        print("=" * 60)
        print(f"命令执行失败: {err}")
        sys.exit(1)
