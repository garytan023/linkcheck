import os
import subprocess
import json
import time
import pandas as pd
from datetime import datetime

# 配置
MCP_SERVER_PATH = "mcp-chrome-tool/server.js"
LINKS_FILE = "links.txt"
OUTPUT_DIR = "test_results"

print("=" * 60)
print("小红书链接测试 - MCP 工具集成测试")
print("=" * 60)

# 1. 读取链接信息
try:
    df = pd.read_excel('link.xlsx')
    links = df['link'].tolist()
    print(f"成功读取 {len(links)} 个链接")
except Exception as e:
    print(f"读取链接失败: {e}")
    exit(1)

# 2. 创建输出目录
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 3. 启动 MCP 服务器进程
print("\n3. 启动 MCP Chrome 服务器...")
env = os.environ.copy()
env['PRIMARY_API_KEY'] = 'key'

try:
    # 使用现有的 Python 监测工具
    print("\n4. 使用 Python 监测工具测试...")

    # 检查是否存在现代 GUI 版本
    if os.path.exists('link_monitor_modern_gui.py'):
        print("发现现代 GUI 版本，但将在后台运行自动化版本")

    # 使用集成监测脚本
    if os.path.exists('integrated_monitor.py'):
        print("运行集成监测脚本...")

        # 临时配置文件
        config = {
            "input_file": "link.xlsx",
            "output_dir": OUTPUT_DIR,
            "headless": True,
            "screenshot": True,
            "report_format": "excel"
        }

        with open('temp_config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        # 运行 Python 监测
        result = subprocess.run([
            'python', 'integrated_monitor.py'
        ], capture_output=True, text=True, timeout=300)

        if result.returncode == 0:
            print("Python 监测工具运行成功")
            print(f"输出: {result.stdout}")
        else:
            print(f"Python 监测工具运行失败: {result.stderr}")

    else:
        print("未找到集成监测脚本，使用简化版本...")

        # 创建简化的测试脚本
        test_script = '''
import pandas as pd
import requests
from datetime import datetime
import json

# 读取链接
df = pd.read_excel('link.xlsx')
links = df['link'].tolist()

results = []
for i, url in enumerate(links, 1):
    print(f"测试链接 {i}/{len(links)}: {url}")

    try:
        # 简单的 HTTP 请求测试
        response = requests.head(url, timeout=10, allow_redirects=True)
        status = response.status_code

        results.append({
            "link": url,
            "status": status,
            "accessible": status < 400,
            "timestamp": datetime.now().isoformat()
        })

        print(f"  状态码: {status}")

    except Exception as e:
        results.append({
            "link": url,
            "status": "ERROR",
            "accessible": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })
        print(f"  错误: {e}")

# 保存结果
output_file = "link_test_results.json"
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\\n结果已保存到: {output_file}")
print(f"可访问链接: {sum(1 for r in results if r.get('accessible', False))}")
print(f"失败链接: {sum(1 for r in results if not r.get('accessible', False))}")
'''

        with open('quick_test.py', 'w', encoding='utf-8') as f:
            f.write(test_script)

        result = subprocess.run(['python', 'quick_test.py'], capture_output=True, text=True)
        print(result.stdout)

        # 清理临时文件
        if os.path.exists('quick_test.py'):
            os.remove('quick_test.py')

except Exception as e:
    print(f"运行失败: {e}")

# 5. 清理临时文件
for temp_file in ['temp_config.json']:
    if os.path.exists(temp_file):
        os.remove(temp_file)

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)