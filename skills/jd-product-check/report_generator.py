#!/usr/bin/env python3
"""
京东商品对比报告生成工具
用于生成对比报告的 Markdown/HTML/飞书文档
"""

import re
from datetime import datetime


def markdown_to_html(md: str, title: str = "京东商品报告") -> str:
    """Markdown 转 HTML"""
    
    def process_lines(lines):
        result = []
        in_table = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 标题
            if line.startswith('### '):
                result.append(f'<h3>{line[4:]}</h3>')
            elif line.startswith('## '):
                result.append(f'<h2>{line[3:]}</h2>')
            elif line.startswith('# '):
                result.append(f'<h1>{line[2:]}</h1>')
            # 表格
            elif '|' in line:
                if not in_table:
                    result.append('<table>')
                    in_table = True
                cells = [c.strip() for c in line.split('|') if c.strip()]
                # 跳过表格分隔行
                if cells and all(c in ['---', ':--', '--:', ':---', '---:', '|'] or (c.count('-') > 0 and c.count(':') <= 2) for c in cells):
                    continue
                tag = 'th' if '分数' in line or '维度' in line or '状态' in line else 'td'
                row = '<tr>' + ''.join(f'<{tag}>{c}</{tag}>' for c in cells) + '</tr>'
                result.append(row)
            else:
                if in_table:
                    result.append('</table>')
                    in_table = False
                # 列表
                if line.startswith('- '):
                    result.append(f'<li>{line[2:]}</li>')
                else:
                    # 格式
                    line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
                    line = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', line)
                    result.append(f'<p>{line}</p>')
        
        if in_table:
            result.append('</table>')
        return '\n'.join(result)
    
    html_content = process_lines(md.split('\n'))
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; background: #f5f5f5; padding: 20px; }}
        .container {{ max-width: 900px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.1); padding: 32px; }}
        h1 {{ color: #1a1a1a; font-size: 28px; margin-bottom: 24px; padding-bottom: 16px; border-bottom: 2px solid #e0e0e0; }}
        h2 {{ color: #2a2a2a; font-size: 20px; margin: 24px 0 16px; }}
        h3 {{ color: #3a3a3a; font-size: 16px; margin: 16px 0 12px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 14px; }}
        th, td {{ padding: 10px 12px; text-align: left; border: 1px solid #e0e0e0; }}
        th {{ background: #f8f8f8; font-weight: 600; }}
        tr:nth-child(even) {{ background: #fafafa; }}
        ul {{ margin: 12px 0; padding-left: 24px; }}
        li {{ margin: 6px 0; }}
        a {{ color: #1890ff; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .footer {{ margin-top: 32px; padding-top: 16px; border-top: 1px solid #e0e0e0; text-align: center; color: #999; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        {html_content}
        <div class="footer">
            由 拉小码 AI 生成 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
</body>
</html>"""
    return html


def save_html(html: str, filename: str = None) -> str:
    """保存 HTML 到文件"""
    import os
    if filename is None:
        filename = f"jd_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    filepath = os.path.join("/tmp", filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    return filepath


async def save_to_feishu(markdown: str, title: str) -> str:
    """保存到飞书云文档"""
    try:
        from feishu_create_doc import create_doc
        doc_url = await create_doc(title=title, markdown=markdown)
        return doc_url
    except Exception as e:
        print(f"飞书文档创建失败: {e}")
        return None


if __name__ == "__main__":
    # 测试
    test_md = """# 测试报告

## 基本信息

| 维度 | 商品1 | 商品2 |
|------|-------|-------|
| 价格 | ¥100 | ¥200 |
| 评分 | 90 | 80 |

## 结论

- 商品1 **胜出**
"""
    
    html = markdown_to_html(test_md, "测试报告")
    path = save_html(html, "test.html")
    print(f"HTML saved to: {path}")
