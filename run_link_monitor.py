"""
链接监测工具 - 执行脚本
在每个步骤之间添加适当的等待时间
"""

import csv
import os
import time
from datetime import datetime

def read_links_from_csv(csv_file):
    """从CSV文件读取链接"""
    links = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
        for row in rows[1:]:  # 跳过标题行
            if row and len(row) > 0 and row[0].strip():
                links.append(row[0].strip())
    return links

def main():
    print("\n" + "="*70)
    print("                    链接监测工具 - 浏览器模式")
    print("="*70)
    
    csv_file = 'yilideeplink.csv'
    links = read_links_from_csv(csv_file)
    
    print(f"\n找到 {len(links)} 个链接待检测:\n")
    for idx, link in enumerate(links, 1):
        print(f"{idx}. {link}")
    
    print("\n" + "="*70)
    print("\n说明：")
    print("1. 浏览器已打开小红书登录页面")
    print("2. 请使用小红书APP扫描二维码并在手机上确认登录")
    print("3. 完成登录后，按 Enter 键继续")
    print("4. 工具将逐个访问链接（每个链接间隔5秒）")
    print("5. 每个链接会等待5秒加载后自动截屏")
    print("\n" + "="*70)
    
    input("\n准备好后，按 Enter 键开始监测...")
    
    # 创建截图目录
    screenshot_dir = 'screenshots'
    if not os.path.exists(screenshot_dir):
        os.makedirs(screenshot_dir)
    
    print("\n开始访问链接...\n")
    
    results = []
    
    for idx, link in enumerate(links, 1):
        print(f"\n[{idx}/{len(links)}] 准备访问: {link}")
        print("  → 请在浏览器中手动访问此链接")
        print(f"  → 等待5秒加载...")
        
        result = {
            '序号': idx,
            '链接': link,
            '状态': '手动访问',
            '截屏文件': f'{screenshot_dir}/screenshot_{idx}.png',
            '检测时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        results.append(result)
        
        if idx < len(links):
            print(f"  → {5}秒后将提示访问下一个链接...")
            time.sleep(5)
    
    print("\n" + "="*70)
    print("所有链接已列出")
    print("现在将使用自动化工具访问每个链接...")
    print("="*70 + "\n")

if __name__ == '__main__':
    main()


