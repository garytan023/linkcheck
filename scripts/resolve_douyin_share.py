#!/usr/bin/env python3
"""
抖音分享落地链接解析器
功能：把任意抖音链接（短链/长链/modal_id）解析为落地分享URL
方法：curl -L 跟踪重定向，无需cookies（v.douyin.com短链是公开的）

用法：
    python3 resolve_douyin_share.py "https://v.douyin.com/xxx"
    python3 resolve_douyin_share.py "https://www.douyin.com/video/7564648507513015602"
    python3 resolve_douyin_share.py "7564648507513015602"
"""
import subprocess, re, json, sys

def resolve_url(url: str) -> str:
    """用curl跟踪重定向，返回最终URL"""
    cmd = [
        "curl", "-sL", "--max-redirs", "5",
        "-w", "%{url_effective}",
        "-o", "/dev/null",
        "-A", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        url
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    return result.stdout.strip()

def extract_modal_id(url: str) -> str:
    """从各种抖音URL格式中提取modal_id"""
    patterns = [
        r'douyin\.com/video/(\d+)',
        r'iesdouyin\.com/share/video/(\d+)',
        r'v\.douyin\.com/([A-Za-z0-9_-]+)',
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    # 纯数字ID
    if re.match(r'^\d+$', url):
        return url
    return None

def resolve_share_link(input_url: str) -> dict:
    """
    主入口：输入任意抖音URL → 落地分享链接
    """
    input_url = input_url.strip()
    
    # 1. 提取modal_id
    modal_id = extract_modal_id(input_url)
    
    if not modal_id:
        return {"success": False, "input": input_url, "error": "无法识别格式"}
    
    # 2. 如果是v.douyin.com短链，用curl解析最终URL
    if "v.douyin.com" in input_url:
        final_url = resolve_url(input_url)
        # 从最终URL再次提取modal_id（确保一致性）
        final_modal_id = extract_modal_id(final_url)
        share_link = f"https://www.iesdouyin.com/share/video/{final_modal_id}/"
        return {
            "success": True,
            "input": input_url,
            "modal_id": final_modal_id,
            "final_url": final_url,
            "share_link": share_link,
        }
    
    # 3. 已经是长链，直接构造落地链接
    share_link = f"https://www.iesdouyin.com/share/video/{modal_id}/"
    return {
        "success": True,
        "input": input_url,
        "modal_id": modal_id,
        "share_link": share_link,
    }

if __name__ == "__main__":
    if len(sys.argv) > 1:
        urls = sys.argv[1:]
    else:
        # 演示
        urls = [
            "https://v.douyin.com/GtUxgH8Jyrc/",
            "https://www.douyin.com/video/7564648507513015602",
        ]
    
    for url in urls:
        r = resolve_share_link(url)
        print(f"\n输入: {url}")
        print(f"  modal_id: {r.get('modal_id')}")
        print(f"  落地链接: {r.get('share_link')}")
        if not r["success"]:
            print(f"  错误: {r.get('error')}")
