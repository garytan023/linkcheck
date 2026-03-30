#!/usr/bin/env python3
"""
记忆系统 - 每日 HOT 层清理脚本
自动清理 HOT_MEMORY.md 中已完成的任务
"""

import re
import os
from datetime import datetime

HOT_MEMORY_PATH = os.path.expanduser("~/.openclaw/workspace-dev/memory/hot/HOT_MEMORY.md")
BACKUP_DIR = os.path.expanduser("~/.openclaw/workspace-dev/memory/hot/backups")

def ensure_backup_dir():
    """确保备份目录存在"""
    os.makedirs(BACKUP_DIR, exist_ok=True)

def backup_file():
    """备份当前文件"""
    if os.path.exists(HOT_MEMORY_PATH):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(BACKUP_DIR, f"HOT_MEMORY_{timestamp}.md")
        with open(HOT_MEMORY_PATH, 'r') as f:
            content = f.read()
        with open(backup_path, 'w') as f:
            f.write(content)
        print(f"📦 已备份到: {backup_path}")

def parse_and_clean(content):
    """
    解析 HOT_MEMORY.md，清理已完成任务
    - 移除 [x] 或 [X] 标记的任务
    - 保留未完成的任务
    """
    lines = content.split('\n')
    cleaned_lines = []
    removed_count = 0
    
    for line in lines:
        # 检查是否为已完成任务行
        # 匹配模式: - [x] 或 - [X] 或 - [✓]
        if re.match(r'^(\s*)-\s*\[[xX✓✓]\]\s', line):
            removed_count += 1
            continue
        cleaned_lines.append(line)
    
    # 移除多余的空行（保留最多2个连续空行）
    result_lines = []
    prev_empty = False
    for line in cleaned_lines:
        is_empty = line.strip() == ''
        if is_empty and prev_empty:
            continue
        result_lines.append(line)
        prev_empty = is_empty
    
    return '\n'.join(result_lines), removed_count

def update_last_updated(content):
    """更新时间戳"""
    lines = content.split('\n')
    result_lines = []
    found_timestamp = False
    
    for line in lines:
        # 找到最后更新时间行并更新
        if '最后更新' in line or 'Last updated' in line.lower():
            result_lines.append(f"**最后更新**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            found_timestamp = True
        else:
            result_lines.append(line)
    
    # 如果没找到时间戳，添加一个
    if not found_timestamp:
        result_lines.insert(0, f"**最后更新**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    
    return '\n'.join(result_lines)

def main():
    print("🧠 记忆系统 - 每日 HOT 层清理")
    print("=" * 40)
    
    if not os.path.exists(HOT_MEMORY_PATH):
        print("❌ HOT_MEMORY.md 不存在")
        return
    
    # 读取当前内容
    with open(HOT_MEMORY_PATH, 'r') as f:
        content = f.read()
    
    print(f"📄 当前文件大小: {len(content)} 字符")
    
    # 备份
    ensure_backup_dir()
    backup_file()
    
    # 清理已完成任务
    cleaned_content, removed_count = parse_and_clean(content)
    
    if removed_count == 0:
        print("✅ 没有已完成的任务需要清理")
        return
    
    # 更新时间戳
    cleaned_content = update_last_updated(cleaned_content)
    
    # 写入清理后的内容
    with open(HOT_MEMORY_PATH, 'w') as f:
        f.write(cleaned_content)
    
    print(f"✅ 已清理 {removed_count} 个已完成任务")
    print(f"📄 清理后文件大小: {len(cleaned_content)} 字符")

if __name__ == "__main__":
    main()
