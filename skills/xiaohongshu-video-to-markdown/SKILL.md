---
name: xiaohongshu-video-to-markdown
description: Download Xiaohongshu/XHS videos, extract audio, transcribe speech locally with whisper.cpp, and produce Obsidian-friendly Markdown notes. Use when the user sends a 小红书视频链接 and wants 下载视频、抽音频、转文字、整理成 markdown、放进 Obsidian/Inbox, especially when MCP/agent-reach can provide note metadata and yt-dlp should do the real download.
---

# 小红书视频转文字 Skill

处理顺序固定，不要乱：

1. **先拿元数据**
   - 优先用 MCP / agent-reach / xiaohongshu-mcp 拿：`note_id`、`xsec_token`、标题、作者、描述。
   - 不要把 xiaohongshu-mcp 当下载器。它负责搜和读详情，不负责稳定下载视频。
   - 如果详情接口因为评论加载挂掉，优先关闭评论加载或只拿主内容。

2. **再下视频**
   - 真下载统一走 `yt-dlp`。
   - 优先命令思路：
     - `yt-dlp --cookies-from-browser chrome <url>`
   - 如果不带 cookie 也能下，就不用强上 cookie。
   - 下载前先 probe；下载后确认文件真实落盘。

3. **抽音频**
   - 统一用 `ffmpeg` 从 mp4 抽 mp3。
   - 输出目录默认放在目标 vault 的 `Inbox/xhs-media/` 下。

4. **转写**
   - 优先用 `whisper.cpp` 的 `whisper-cli`，不要默认写成 `whisper`。
   - 当前环境已确认可执行路径：`/opt/homebrew/bin/whisper-cli`
   - 优先检查模型是否存在。已知可用模型候选：
     - `/Users/garytan/whisper-models/ggml-large-v3-turbo/ggml-large-v3-turbo.bin`
     - `/Users/garytan/.whisper/ggml-medium.bin`
     - `/Users/garytan/.whisper/ggml-base.bin`
     - `/Users/garytan/.local/share/whisper/ggml-base.bin`
   - 优先顺序：large-v3-turbo > medium > base。

5. **整理成 Markdown**
   - 至少输出这几块：
     - 标题
     - 来源链接
     - note_id / 作者 / 发布时间（能拿到就写）
     - 一句话总结
     - 技巧整理 / 内容结构化总结
     - 原始转写
   - 输出必须是 Obsidian 友好的 Markdown。

6. **落到 Obsidian**
   - 默认目标 vault：`/Users/garytan/Documents/garytan/宇先生`
   - 默认 Inbox：`/Users/garytan/Documents/garytan/宇先生/Inbox`
   - 默认媒体目录：`/Users/garytan/Documents/garytan/宇先生/Inbox/xhs-media`

## 当前环境固定记忆

### 标准链路
- `MCP / agent-reach`：负责找笔记与拿元数据
- `yt-dlp`：负责真下载视频
- `ffmpeg`：负责抽音频
- `whisper.cpp`：负责转写
- `Markdown / Obsidian`：负责沉淀结果

一句话：
**小红书：MCP 负责找，yt-dlp 负责下，whisper.cpp 负责转。**

## 执行前检查

先检查这些：
- `yt-dlp` 是否可用
- `ffmpeg` 是否可用
- `/opt/homebrew/bin/whisper-cli` 是否可用
- 至少一个 ggml 模型是否存在
- 目标 vault / Inbox 路径是否存在

## 常见坑

### 1) `whisper: command not found`
不是没装 ASR，而是很可能装的是 `whisper.cpp`，命令要改成：
- `/opt/homebrew/bin/whisper-cli`

### 2) MCP 能搜不能下
这是正常情况。不要死磕 MCP 下载。直接切 `yt-dlp`。

### 3) xiaohongshu-mcp 详情接口挂在评论加载
如果出现评论区滚动崩溃，不要继续耗。先关闭评论加载，只拿主内容元数据。

### 4) cookie 半失效
如果 search 可以、detail 不稳定、下载链异常，再考虑更新 cookie；但下载优先先试 `yt-dlp --cookies-from-browser chrome`。

## 输出标准

最终交付至少包括：
- 视频文件
- 音频文件
- 转写 txt
- 整理后的 Markdown

如果用户明确要“技巧总结”，不要只给原始转写，必须加结构化总结。
