#!/usr/bin/env python3
"""
OpenClaw 定时备份脚本
每天凌晨自动备份 workspace 到 GitHub
"""

import os
import subprocess
from datetime import datetime

WORKSPACE = "/Users/garytan/.openclaw/workspace-dev"
BACKUP_LOG = "/tmp/openclaw_backup.log"

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {msg}\n"
    with open(BACKUP_LOG, "a") as f:
        f.write(log_msg)
    print(log_msg.strip())

def run_cmd(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr

def main():
    log("开始备份 OpenClaw workspace...")
    
    # 检查是否有变化
    rc, stdout, stderr = run_cmd("git status --porcelain", cwd=WORKSPACE)
    if rc != 0:
        log(f"Git error: {stderr}")
        return
    
    if not stdout.strip():
        log("没有变化，跳过备份")
        return
    
    # Add 所有变化
    rc, stdout, stderr = run_cmd("git add -A", cwd=WORKSPACE)
    if rc != 0:
        log(f"Git add error: {stderr}")
        return
    
    # Commit
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    commit_msg = f"Auto backup: {date_str}"
    rc, stdout, stderr = run_cmd(f'git commit -m "{commit_msg}"', cwd=WORKSPACE)
    if rc != 0:
        if "nothing to commit" in stderr:
            log("没有变化，跳过")
            return
        log(f"Git commit error: {stderr}")
        return
    
    # Push
    rc, stdout, stderr = run_cmd("git push origin main", cwd=WORKSPACE)
    if rc != 0:
        log(f"Git push error: {stderr}")
        return
    
    log("备份完成 ✓")

if __name__ == "__main__":
    main()
