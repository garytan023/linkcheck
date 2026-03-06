import pandas as pd
import sys

try:
    # 读取 Excel 文件
    df = pd.read_excel('link.xlsx')

    print(f"链接数量: {len(df)}")
    print(f"\n列名: {list(df.columns)}")
    print("\n前5行数据:")
    print(df.head())

    # 检查第一列是否包含链接
    first_column = df.iloc[:, 0]
    print(f"\n第一列名称: {df.columns[0]}")
    print("\n所有链接:")

    for i, url in enumerate(first_column, 1):
        print(f"{i}. {url}")

    # 保存链接到文本文件便于后续处理
    with open('links.txt', 'w', encoding='utf-8') as f:
        for url in first_column:
            f.write(f"{url}\n")

    print(f"\n已保存 {len(first_column)} 个链接到 links.txt 文件")

except Exception as e:
    print(f"错误: {e}")
    sys.exit(1)