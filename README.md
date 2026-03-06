# 链接监测工具 Pro

一个功能完善的链接监测工具（Pro 版），带有图形化界面，支持批量监测网页链接、自动截图并生成Excel报告。当前版本特性：
- 持久化登录：默认使用 `xhs_pro_profile` 目录保存登录态，扫码一次后后续可复用
- 截图+封面：Excel 先展示截图，再展示最多 10 张封面，并新增封面 URL 列表与 URL1-10（图文/视频都能覆盖）
- 粉丝数兜底：悬停 + 全文搜索 + API + 主页兜底

## 功能特性

✅ **图形化界面** - 简洁易用的GUI界面
✅ **文件选择** - 支持选择输入CSV文件和输出目录
✅ **批量监测** - 批量访问CSV中的所有链接
✅ **自动截图** - 自动对每个链接进行截屏
✅ **Excel报告** - 生成包含截图的详细Excel报告
✅ **定时任务** - 支持设置定时自动运行
✅ **实时进度** - 显示实时处理进度和日志
✅ **错误处理** - 记录失败链接并在报告中标注

## Windows 一键运行（EXE）

1) 直接运行  
   双击 `dist/WPP_MD_链接监测工具_Pro.exe`（已内置 Python 和 Chromium，免安装依赖/浏览器）。按界面选择 `yilideeplink.csv` 和输出目录（默认 `./output`），登录一次后可复用。

## Windows 一键运行（Ultimate v4）

1) 直接运行  
   双击 `dist/WPP_MD_链接监测工具_Ultimate_v4.exe`（已内置 Python 和 Chromium）。按界面选择 CSV 与输出目录。
2) 飞书同步  
   如需飞书多维表格同步，将 `feishu_config.json` 放在 EXE 同目录并配置后再运行。

## 源码运行（Pro GUI）

### 安装依赖

```bash
pip install -r requirements.txt
```

依赖包括：
- `openpyxl` - Excel文件操作
- `Pillow` - 图片处理
- `playwright` - 浏览器自动化
- `schedule` - 定时任务

### 启动

```bash
python link_monitor_pro_gui.py
```

### 2. 配置参数

#### 文件设置
- **输入CSV**: 选择包含链接的CSV文件（默认：yilideeplink.csv）
- **输出目录**: 选择报告和截图保存位置（默认：./output）

#### 定时任务
- **启用定时运行**: 勾选后可设置每天定时运行
- **运行时间**: 设置运行时间，格式为 HH:MM（如 09:00）

### 3. 开始监测

点击"立即开始监测"按钮开始处理链接。

### 4. 查看结果

- **实时日志**: 界面下方显示实时处理日志
- **进度条**: 显示当前处理进度
- **Excel报告**: 完成后自动生成带时间戳的Excel报告

## CSV文件格式

输入CSV文件格式示例：

```csv
链接
https://www.xiaohongshu.com/explore/xxx
https://www.xiaohongshu.com/explore/yyy
```

## 输出文件

监测完成后会在输出目录生成以下文件：

```
output/
├── 链接监测报告_20231122_143052.xlsx  # Excel报告
└── screenshots/                      # 截图文件夹
    ├── screenshot_1.png
    ├── screenshot_2.png
    └── ...
```

## Excel报告内容

生成的Excel报告包含：

| 序号 | 链接 | 状态 | 截屏预览 | 检测时间 |
|------|------|------|----------|----------|
| 1 | https://... | 成功/失败 | [截图] | 2023-11-22 14:30:52 |

- **绿色**：成功访问
- **红色**：访问失败
- **截图**：直接嵌入Excel中，方便查看

## 高级功能

### 定时任务

启用定时任务后，工具会：
1. 在指定时间自动运行监测
2. 生成带时间戳的报告
3. 记录每次运行的日志

### 浏览器截图（需要Playwright）

首次使用需要安装Playwright浏览器：

```bash
playwright install chromium
```

## 命令行版本

如果不需要GUI界面，也可以使用命令行版本：

```bash
python link_monitor_full.py
```

## 常见问题

### 1. 截图文件不存在
- 确保已安装Playwright并执行了 `playwright install`
- 检查链接是否需要登录才能访问

### 2. CSV文件读取失败
- 确保CSV文件编码为UTF-8
- 检查文件格式是否正确（第一行为"链接"标题）

### 3. Excel报告生成失败
- 确保输出目录有写入权限
- 检查截图文件是否存在

## 技术栈

- **Python 3.8+**
- **tkinter** - GUI界面
- **Playwright** - 浏览器自动化
- **openpyxl** - Excel操作
- **Pillow** - 图片处理
- **schedule** - 定时任务

## 项目结构

```
linkcheck/
├── link_monitor_gui.py          # GUI主程序
├── link_monitor_full.py         # 命令行版本
├── yilideeplink.csv            # 示例CSV文件
├── requirements.txt            # 依赖列表
├── README.md                   # 说明文档
└── output/                     # 输出目录
    ├── screenshots/            # 截图文件
    └── *.xlsx                  # Excel报告
```

## 重新打包 EXE

已生成：`dist/WPP_MD_链接监测工具_Pro.exe`  
如需重新打包（Windows PowerShell）：
```powershell
py -3 build_exe.py
```
或运行 `python build_exe.py`（已改为 Pro 版）。

### 重新打包 Ultimate v4

已生成：`dist/WPP_MD_链接监测工具_Ultimate_v4.exe`  
重新打包（Windows PowerShell）：
```powershell
py -3 build_ultimate_v4_exe.py
```
或运行 `python build_ultimate_v4_exe.py`。

## 许可证

MIT License

## 作者

Created by AI Assistant

---

**提示**: 首次使用建议先用小量链接测试，确认一切正常后再进行大批量监测。








