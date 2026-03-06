"""
构建 Ultimate v4 版本 EXE 的脚本。
会将 link_monitor_ultimate_v4.py 打包成独立 EXE，并把 Playwright 浏览器一并打包。
"""

import os
import subprocess
import sys
import time
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

    build_start_ts = time.time()
    run_command(cmd)

    # 兼容 Windows(.exe) 与 Linux/macOS(无扩展名) 输出，并优先选择本次新生成的产物
    output_candidates = [
        os.path.join(dist_dir, f"{exe_name}.exe"),
        os.path.join(dist_dir, exe_name),
    ]
    fresh_outputs = [
        p for p in output_candidates
        if os.path.exists(p) and os.path.getmtime(p) >= (build_start_ts - 2)
    ]
    if fresh_outputs:
        output_path = max(fresh_outputs, key=os.path.getmtime)
    else:
        default_name = f"{exe_name}.exe" if os.name == "nt" else exe_name
        output_path = os.path.join(dist_dir, default_name)

    size_mb = os.path.getsize(output_path) / (1024 * 1024) if os.path.exists(output_path) else None
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print()
    print("=" * 60)
    print("[成功] Ultimate v4 打包完成")
    print("=" * 60)
    print(f"[时间] {timestamp}")
    print(f"[输出] {output_path}")
    if size_mb:
        print(f"[大小] {size_mb:.2f} MB")
    if os.name != "nt":
        print("[注意] 当前是非 Windows 环境，生成的是本机可执行文件（不是 .exe）")
        print("       如需 Windows .exe，请在 Windows 命令行里运行 打包EXE.bat")
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
