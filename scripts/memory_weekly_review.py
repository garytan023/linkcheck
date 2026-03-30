#!/usr/bin/env python3
"""
记忆系统 - 每周 WARM 层回顾脚本
检查 WARM_MEMORY.md 并生成回顾报告
"""

import os
from datetime import datetime
from pathlib import Path

WARM_MEMORY_PATH = os.path.expanduser("~/.openclaw/workspace-dev/memory/warm/WARM_MEMORY.md")
MEMORY_DIR = os.path.expanduser("~/.openclaw/workspace-dev/memory")
REVIEW_REPORT_PATH = os.path.expanduser("~/.openclaw/workspace-dev/memory/weekly_review_report.md")

def get_memory_stats():
    """获取记忆系统统计信息"""
    stats = {
        'hot_files': 0,
        'warm_files': 0,
        'cold_files': 0,
        'total_journals': 0
    }
    
    hot_dir = os.path.join(MEMORY_DIR, 'hot')
    warm_dir = os.path.join(MEMORY_DIR, 'warm')
    
    if os.path.exists(hot_dir):
        stats['hot_files'] = len([f for f in os.listdir(hot_dir) if f.endswith('.md')])
    
    if os.path.exists(warm_dir):
        stats['warm_files'] = len([f for f in os.listdir(warm_dir) if f.endswith('.md')])
    
    # 统计 COLD 层日记数量
    for f in os.listdir(MEMORY_DIR):
        if f.startswith('20') and f.endswith('.md'):
            stats['cold_files'] += 1
    
    return stats

def read_warm_memory():
    """读取 WARM 层内容"""
    if not os.path.exists(WARM_MEMORY_PATH):
        return None
    
    with open(WARM_MEMORY_PATH, 'r') as f:
        return f.read()

def check_preferences_uptodate(content):
    """检查偏好设置是否需要更新"""
    # 检查是否有更新时间
    indicators = ['最后更新', 'Last updated', '更新于']
    needs_update = True
    
    for indicator in indicators:
        if indicator.lower() in content.lower():
            needs_update = False
            break
    
    return needs_update

def check_agent_configs(content):
    """检查 Agent 配置是否有变化"""
    # 检查是否有 Agent 家族信息
    agent_keywords = ['Agent', 'agent', '拉小']
    has_agents = any(kw in content for kw in agent_keywords)
    
    # 检查是否有配置时间
    config_time_keywords = ['配置', 'config', 'workspace']
    has_config_time = any(kw in content for kw in config_time_keywords)
    
    return {
        'has_agent_info': has_agents,
        'has_config_info': has_config_time,
        'needs_review': not (has_agents and has_config_time)
    }

def generate_report():
    """生成每周回顾报告"""
    print("🧠 记忆系统 - 每周 WARM 层回顾")
    print("=" * 50)
    
    stats = get_memory_stats()
    print(f"📊 记忆统计:")
    print(f"   - HOT 层: {stats['hot_files']} 个文件")
    print(f"   - WARM 层: {stats['warm_files']} 个文件")
    print(f"   - COLD 层 (日记): {stats['cold_files']} 个文件")
    
    warm_content = read_warm_memory()
    
    if warm_content:
        print(f"\n📄 WARM_MEMORY.md 大小: {len(warm_content)} 字符")
        
        # 检查偏好是否需要更新
        needs_update = check_preferences_uptodate(warm_content)
        if needs_update:
            print("⚠️  WARM 层可能需要更新 (缺少时间戳)")
        
        # 检查 Agent 配置
        agent_info = check_agent_configs(warm_content)
        if agent_info['needs_review']:
            print("⚠️  建议检查 Agent 配置信息")
        
        # 生成报告
        report = f"""# 每周记忆回顾报告 | {datetime.now().strftime('%Y-%m-%d')}

## 记忆统计
- HOT 层: {stats['hot_files']} 个文件
- WARM 层: {stats['warm_files']} 个文件  
- COLD 层 (日记): {stats['cold_files']} 个文件

## WARM 层状态
- 最后更新检查: {"需要更新" if needs_update else "正常"}
- Agent 配置: {"完整" if not agent_info['needs_review'] else "建议检查"}

## 建议事项
{"- 检查 HOT 层是否有已完成任务需要清理" if stats['hot_files'] > 0 else ""}
{"- 回顾 WARM 层用户偏好是否有变化" if needs_update else ""}
{"- 检查是否有新 Agent 需要添加" if agent_info['needs_review'] else ""}

---
*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        # 写入报告
        with open(REVIEW_REPORT_PATH, 'w') as f:
            f.write(report)
        
        print(f"\n✅ 报告已生成: {REVIEW_REPORT_PATH}")
        
    else:
        print("❌ 无法读取 WARM_MEMORY.md")
    
    print("\n💡 提示: 运行后请检查报告并根据建议更新记忆文件")

if __name__ == "__main__":
    generate_report()
