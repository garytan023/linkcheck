"""
小红书链接监测工具 - FastAPI Web 服务端
提供 REST API 和 WebSocket 接口供前端调用
"""

import asyncio
import csv
import json
import os
import threading
import time
import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pathlib import Path

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

# 导入原监控工具的核心类
# 注意：需要确保 link_monitor_ultimate_v4.py 在同一目录或可导入
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 尝试导入必要的模块
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("Warning: Playwright not installed. Running in simulation mode.")

try:
    from link_monitor_ultimate_v4 import FeishuBitableSync
except ImportError:
    FeishuBitableSync = None

# ============================================================================
# Pydantic 模型定义
# ============================================================================

class TaskStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


class LogLevel(str, Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class LogEntry(BaseModel):
    timestamp: str
    level: str
    message: str


class MonitorConfig(BaseModel):
    # 基本配置
    csv_file: Optional[str] = None
    output_dir: str = "./output_v4"

    # 延迟配置
    link_interval_min: float = 1.5
    link_interval_max: float = 3.5
    page_load_min: float = 1.2
    page_load_max: float = 3.0
    screenshot_delay_min: float = 0.4
    screenshot_delay_max: float = 1.2

    # 性能配置
    concurrent_downloads: int = 3
    download_timeout: int = 30
    cache_enabled: bool = True
    cache_ttl: int = 3600

    # 登录配置
    login_wait_time: int = 60
    login_retries: int = 3

    # 功能开关
    enable_anti_detection: bool = True
    capture_mode: str = "full"  # full 或 basic

    # 飞书配置
    enable_feishu_sync: bool = False
    feishu_app_id: str = ""
    feishu_app_secret: str = ""
    feishu_app_token: str = ""
    feishu_table_id: str = ""


class TaskInfo(BaseModel):
    task_id: str
    status: TaskStatus
    total_links: int
    processed_links: int
    success_count: int
    failed_count: int
    current_link: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class LinkResult(BaseModel):
    序号: str
    产品: str
    链接: str
    笔记ID: str = ""
    采集状态: str = "pending"
    错误信息: str = ""
    标题: str = ""
    作者昵称: str = ""
    作者ID: str = ""
    粉丝数: str = ""
    博主主页: str = ""
    发布时间: str = ""
    点赞数: str = ""
    收藏数: str = ""
    评论数: str = ""
    分享数: str = ""
    封面链接: str = ""
    视频链接: str = ""
    正文: str = ""
    截屏文件: str = ""
    封面图数量: int = 0
    检测时间: str = ""
    登录状态: str = ""
    反爬状态: str = ""


# ============================================================================
# WebSocket 连接管理器
# ============================================================================

class ConnectionManager:
    """管理 WebSocket 连接，支持广播消息"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """向所有连接的客户端广播消息"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)

        # 清理断开的连接
        for conn in disconnected:
            self.disconnect(conn)

    async def send_personal(self, message: dict, websocket: WebSocket):
        """向指定客户端发送消息"""
        try:
            await websocket.send_json(message)
        except Exception:
            self.disconnect(websocket)


manager = ConnectionManager()


# ============================================================================
# 全局状态管理
# ============================================================================

class MonitorState:
    """监控任务状态管理"""

    def __init__(self):
        self.task_id: Optional[str] = None
        self.status: TaskStatus = TaskStatus.IDLE
        self.config: MonitorConfig = MonitorConfig()
        self.links: List[Dict] = []
        self.results: List[Dict] = []
        self.logs: List[LogEntry] = []
        self.stats = {
            "total_links": 0,
            "processed_links": 0,
            "success_count": 0,
            "failed_count": 0,
            "anti_crawler_count": 0
        }
        self.started_at: Optional[str] = None
        self.completed_at: Optional[str] = None
        self.current_link: Optional[str] = None
        self._stop_flag = False
        self._pause_flag = False
        self._worker_thread: Optional[threading.Thread] = None

    def reset(self):
        """重置状态"""
        self.task_id = None
        self.status = TaskStatus.IDLE
        self.links = []
        self.results = []
        self.logs = []
        self.stats = {
            "total_links": 0,
            "processed_links": 0,
            "success_count": 0,
            "failed_count": 0,
            "anti_crawler_count": 0
        }
        self.started_at = None
        self.completed_at = None
        self.current_link = None
        self._stop_flag = False
        self._pause_flag = False

    def add_log(self, level: str, message: str):
        """添加日志"""
        entry = LogEntry(
            timestamp=datetime.now().strftime("%H:%M:%S"),
            level=level,
            message=message
        )
        self.logs.append(entry)
        # 限制日志数量
        if len(self.logs) > 1000:
            self.logs = self.logs[-1000:]

    def should_stop(self) -> bool:
        """检查是否应该停止"""
        return self._stop_flag

    def should_pause(self) -> bool:
        """检查是否应该暂停"""
        return self._pause_flag

    def stop(self):
        """设置停止标志"""
        self._stop_flag = True

    def pause(self):
        """设置暂停标志"""
        self._pause_flag = True

    def resume(self):
        """清除暂停标志"""
        self._pause_flag = False


# 全局状态实例
state = MonitorState()


# ============================================================================
# FastAPI 应用初始化
# ============================================================================

app = FastAPI(
    title="小红书链接监测工具 API",
    description="提供小红书链接采集、数据提取、Excel 导出等功能",
    version="4.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应设置具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# 辅助函数
# ============================================================================

def broadcast_log(level: str, message: str):
    """广播日志到所有 WebSocket 客户端"""
    state.add_log(level, message)
    # 在异步上下文中需要使用 asyncio.create_task


def broadcast_status():
    """广播状态更新到所有 WebSocket 客户端"""
    return {
        "type": "status",
        "data": {
            "task_id": state.task_id,
            "status": state.status.value,
            "stats": state.stats,
            "current_link": state.current_link,
            "started_at": state.started_at,
            "completed_at": state.completed_at
        }
    }


def broadcast_progress():
    """广播进度更新"""
    return {
        "type": "progress",
        "data": {
            "processed": state.stats["processed_links"],
            "total": state.stats["total_links"],
            "success": state.stats["success_count"],
            "failed": state.stats["failed_count"],
            "percent": int(state.stats["processed_links"] / state.stats["total_links"] * 100) if state.stats["total_links"] > 0 else 0
        }
    }


def parse_csv_file(file_path: str) -> List[Dict]:
    """解析 CSV 文件"""
    links = []
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            if reader.fieldnames and ('链接' in reader.fieldnames or reader.fieldnames[0]):
                for idx, row in enumerate(reader, 1):
                    link = (row.get('链接') or row.get(reader.fieldnames[0]) or '').strip()
                    if not link:
                        continue
                    links.append({
                        '产品': row.get('产品', '').strip(),
                        '序号': row.get('序号', '').strip() or str(idx),
                        '链接': link
                    })
    except Exception:
        # 尝试简单格式
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            rows = list(reader)
            for idx, row in enumerate(rows[1:], 1):
                if row and len(row) > 0 and row[0].strip():
                    links.append({
                        '产品': '',
                        '序号': str(idx),
                        '链接': row[0].strip()
                    })
    return links


# ============================================================================
# 真实监控任务（使用 Playwright）
# ============================================================================

def extract_note_id(url):
    """从 URL 中提取笔记 ID"""
    import re
    patterns = [
        r'/explore/([a-f0-9]+)',
        r'/discovery/item/([a-f0-9]+)',
        r'/item/([a-f0-9]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return ""


def real_scrape_page(page, url, log_callback):
    """真实采集单个页面数据"""
    result = {
        "笔记ID": extract_note_id(url),
        "标题": "",
        "作者昵称": "",
        "作者ID": "",
        "粉丝数": "",
        "博主主页": "",
        "发布时间": "",
        "点赞数": "",
        "收藏数": "",
        "评论数": "",
        "分享数": "",
        "封面链接": "",
        "视频链接": "",
        "正文": "",
        "封面图数量": 0
    }

    try:
        log_callback("info", f"正在访问: {url}")

        # 访问页面
        page.goto(url, wait_until="networkidle", timeout=30000)
        time.sleep(2)

        # 提取页面数据
        page_data = page.evaluate("""
            () => {
                const pick = (...values) => {
                    for (const val of values) {
                        if (val !== undefined && val !== null && val !== '') return val;
                    }
                    return '';
                };

                const result = {
                    title: '',
                    authorName: '',
                    authorId: '',
                    content: '',
                    likes: '',
                    collects: '',
                    comments: '',
                    publishTime: ''
                };

                const globalState = window.__INITIAL_STATE__ || window.__REDUX_STATE__ || {};
                const noteStore = globalState.note || globalState.noteDetail || {};
                const detailMap = noteStore.noteDetailMap || noteStore.notes || {};

                let detail = null;
                const values = Object.values(detailMap);
                if (values.length > 0) detail = values[0];

                if (detail) {
                    const note = detail.note || detail;
                    const user = detail.user || note.user || {};
                    const stats = detail.noteStat || detail.interactInfo || {};

                    result.title = (note.title || '').trim();
                    result.content = (note.desc || '').trim();
                    result.publishTime = pick(note.time, note.publish_time);

                    result.authorName = pick(user.nickname, user.nick_name);
                    const authorId = pick(user.user_id, user.id);
                    if (authorId) result.authorId = authorId.toString();

                    result.likes = pick(stats.likes, stats.likeCount, stats.likedCount);
                    result.collects = pick(stats.collectCount, stats.favoriteCount);
                    result.comments = pick(stats.commentCount);
                }

                return result;
            }
        """)

        # 填充结果
        result["标题"] = (page_data.get("title") or "")[:200]
        result["正文"] = (page_data.get("content") or "")[:500]
        result["作者昵称"] = page_data.get("authorName") or ""
        result["作者ID"] = page_data.get("authorId") or ""
        result["博主主页"] = f"https://www.xiaohongshu.com/user/profile/{result['作者ID']}" if result["作者ID"] else ""
        result["发布时间"] = page_data.get("publishTime") or ""
        result["点赞数"] = str(page_data.get("likes", ""))
        result["收藏数"] = str(page_data.get("collects", ""))
        result["评论数"] = str(page_data.get("comments", ""))

        # 提取图片
        try:
            images = page.evaluate("""
                () => {
                    const imgs = document.querySelectorAll('img[src*="sns-img"], img[src*="xhscdn"]');
                    return Array.from(imgs).slice(0, 9).map(img => img.currentSrc || img.src).filter(Boolean);
                }
            """)
            if images:
                result["封面链接"] = images[0]
                result["封面图数量"] = len(images)
        except Exception:
            pass

        log_callback("success", "✓ 数据提取成功")
        return result, True

    except Exception as e:
        log_callback("error", f"采集失败: {str(e)}")
        return result, False


def run_monitor_task():
    """运行监控任务（使用真实 Playwright 采集）"""
    import random

    state.status = TaskStatus.RUNNING
    state.started_at = datetime.now().isoformat()
    state.add_log("info", "开始采集任务...")
    state.add_log("info", f"总共 {len(state.links)} 个链接待处理")

    # 检查 Playwright 是否可用
    if not PLAYWRIGHT_AVAILABLE:
        state.add_log("warning", "Playwright 未安装，使用模拟模式")
        # 使用模拟模式
        for idx, link_data in enumerate(state.links):
            if state.should_stop():
                state.add_log("warning", "任务被用户中断")
                state.status = TaskStatus.IDLE
                return

            while state.should_pause():
                time.sleep(0.5)
                if state.should_stop():
                    return

            state.current_link = link_data['链接']
            state.stats["processed_links"] = idx + 1
            time.sleep(random.uniform(1, 3))

            success = random.random() > 0.2
            result = {
                **link_data,
                "笔记ID": f"note_{uuid.uuid4().hex[:8]}",
                "采集状态": "成功" if success else "失败",
                "错误信息": "" if success else "模拟失败",
                "标题": f"【模拟】{link_data.get('产品', '笔记')}" if success else "",
                "作者昵称": f"模拟用户_{random.randint(1000, 9999)}" if success else "",
                "点赞数": str(random.randint(100, 10000)) if success else "",
                "收藏数": str(random.randint(50, 5000)) if success else "",
                "检测时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            state.results.append(result)
            if success:
                state.stats["success_count"] += 1
                state.add_log("success", f"[{idx + 1}/{len(state.links)}] 模拟采集成功")
            else:
                state.stats["failed_count"] += 1
                state.add_log("error", f"[{idx + 1}/{len(state.links)}] 模拟采集失败")

        state.status = TaskStatus.COMPLETED
        state.completed_at = datetime.now().isoformat()
        state.add_log("success", "模拟模式：所有链接处理完成！")
        return

    # 使用真实 Playwright 采集
    state.add_log("info", "正在启动 Playwright 浏览器...")

    try:
        with sync_playwright() as p:
            # 启动浏览器
            browser = p.chromium.launch(
                headless=False,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                ]
            )

            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )

            page = context.new_page()

            state.add_log("success", "✓ 浏览器已启动")

            # 处理每个链接
            for idx, link_data in enumerate(state.links):
                if state.should_stop():
                    state.add_log("warning", "任务被用户中断")
                    break

                # 等待暂停结束
                while state.should_pause():
                    time.sleep(0.5)
                    if state.should_stop():
                        break

                url = link_data['链接']
                state.current_link = url
                state.stats["processed_links"] = idx + 1

                # 定义日志回调
                def log_callback(level, message):
                    state.add_log(level, f"[{idx + 1}/{len(state.links)}] {message}")

                # 采集数据
                details, success = real_scrape_page(page, url, log_callback)

                # 构建结果
                result = {
                    **link_data,
                    "笔记ID": details.get("笔记ID", ""),
                    "采集状态": "成功" if success else "失败",
                    "错误信息": "" if success else "页面加载失败",
                    "标题": details.get("标题", ""),
                    "作者昵称": details.get("作者昵称", ""),
                    "作者ID": details.get("作者ID", ""),
                    "粉丝数": details.get("粉丝数", ""),
                    "博主主页": details.get("博主主页", ""),
                    "发布时间": details.get("发布时间", ""),
                    "点赞数": details.get("点赞数", ""),
                    "收藏数": details.get("收藏数", ""),
                    "评论数": details.get("评论数", ""),
                    "分享数": details.get("分享数", ""),
                    "封面链接": details.get("封面链接", ""),
                    "视频链接": details.get("视频链接", ""),
                    "正文": details.get("正文", ""),
                    "封面图数量": details.get("封面图数量", 0),
                    "检测时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

                state.results.append(result)

                if success:
                    state.stats["success_count"] += 1
                else:
                    state.stats["failed_count"] += 1

                # 随机延迟
                if idx < len(state.links) - 1:
                    delay = random.uniform(1.5, 3.5)
                    time.sleep(delay)

            browser.close()

    except Exception as e:
        state.add_log("error", f"浏览器异常: {str(e)}")
        state.status = TaskStatus.ERROR
        return

    state.status = TaskStatus.COMPLETED
    state.completed_at = datetime.now().isoformat()
    state.add_log("success", f"采集完成！成功: {state.stats['success_count']}, 失败: {state.stats['failed_count']}")


# ============================================================================
# REST API 路由
# ============================================================================

@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "小红书链接监测工具 API",
        "version": "4.0.0",
        "status": "running"
    }


@app.get("/api/status")
async def get_status():
    """获取当前状态"""
    return {
        "task_id": state.task_id,
        "status": state.status.value,
        "stats": state.stats,
        "config": state.config.dict(),
        "current_link": state.current_link,
        "started_at": state.started_at,
        "completed_at": state.completed_at
    }


@app.get("/api/logs")
async def get_logs(limit: int = 100):
    """获取日志"""
    return {"logs": state.logs[-limit:]}


@app.get("/api/results")
async def get_results():
    """获取采集结果"""
    return {
        "results": state.results,
        "total": len(state.results)
    }


@app.post("/api/config")
async def update_config(config: MonitorConfig):
    """更新配置"""
    output_dir = config.output_dir or "./output_v4"
    try:
        os.makedirs(output_dir, exist_ok=True)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"输出目录不可用: {exc}") from exc
    config.output_dir = output_dir
    state.config = config
    # 保存飞书配置
    if config.enable_feishu_sync and FeishuBitableSync:
        feishu = FeishuBitableSync(logger=lambda msg, level: state.add_log(level, msg))
        feishu.update_config({
            "enabled": config.enable_feishu_sync,
            "app_id": config.feishu_app_id,
            "app_secret": config.feishu_app_secret,
            "app_token": config.feishu_app_token,
            "table_id": config.feishu_table_id
        }, persist=True)
    state.add_log("info", "配置已更新")
    return {"success": True}


def _choose_output_dir() -> str:
    try:
        import tkinter as tk
        from tkinter import filedialog
    except Exception as exc:
        raise RuntimeError("tkinter unavailable") from exc

    root = tk.Tk()
    root.withdraw()
    try:
        root.attributes("-topmost", True)
    except Exception:
        pass
    path = filedialog.askdirectory(title="选择输出目录")
    root.destroy()
    return path


@app.get("/api/select-output-dir")
async def select_output_dir():
    """选择输出目录"""
    try:
        path = await asyncio.to_thread(_choose_output_dir)
    except Exception as exc:
        state.add_log("error", f"选择输出目录失败: {exc}")
        return {"success": False, "message": str(exc)}

    if not path:
        return {"success": False, "message": "未选择目录"}

    state.add_log("info", f"输出目录已选择: {path}")
    return {"success": True, "path": path}


@app.post("/api/upload")
async def upload_csv(file: UploadFile = File(...)):
    """上传 CSV 文件"""
    # 保存上传的文件
    upload_dir = "./uploads"
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, f"{int(time.time())}_{file.filename}")

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # 解析 CSV
    try:
        links = parse_csv_file(file_path)
        state.links = links
        state.stats["total_links"] = len(links)
        state.stats["processed_links"] = 0
        state.stats["success_count"] = 0
        state.stats["failed_count"] = 0
        state.results = []
        state.config.csv_file = file_path

        state.add_log("info", f"文件已加载: {file.filename}")
        state.add_log("success", f"解析完成，共 {len(links)} 个链接")

        return {
            "success": True,
            "file_path": file_path,
            "total_links": len(links),
            "links": links[:10]  # 返回前10条作为预览
        }
    except Exception as e:
        state.add_log("error", f"CSV 解析失败: {str(e)}")
        raise HTTPException(status_code=400, detail=f"CSV 解析失败: {str(e)}")


@app.post("/api/start")
async def start_monitor(background_tasks: BackgroundTasks):
    """开始监控任务"""
    if state.status == TaskStatus.RUNNING:
        return {"success": False, "message": "任务正在运行中"}

    if not state.links:
        return {"success": False, "message": "请先上传 CSV 文件"}

    # 重置状态
    state._stop_flag = False
    state._pause_flag = False
    state.task_id = str(uuid.uuid4())
    state.results = []
    state.stats["processed_links"] = 0
    state.stats["success_count"] = 0
    state.stats["failed_count"] = 0

    # 在后台线程中运行任务
    thread = threading.Thread(target=run_monitor_task, daemon=True)
    thread.start()

    return {
        "success": True,
        "task_id": state.task_id,
        "total_links": len(state.links)
    }


@app.post("/api/pause")
async def pause_monitor():
    """暂停/继续监控任务"""
    if state.status != TaskStatus.RUNNING:
        return {"success": False, "message": "没有运行中的任务"}

    if state._pause_flag:
        state.resume()
        state.status = TaskStatus.RUNNING
        state.add_log("info", "采集继续...")
        return {"success": True, "action": "resumed"}
    else:
        state.pause()
        state.status = TaskStatus.PAUSED
        state.add_log("warning", "采集已暂停")
        return {"success": True, "action": "paused"}


@app.post("/api/stop")
async def stop_monitor():
    """停止监控任务"""
    if state.status not in [TaskStatus.RUNNING, TaskStatus.PAUSED]:
        return {"success": False, "message": "没有运行中的任务"}

    state.stop()
    state.add_log("warning", "正在停止任务...")
    return {"success": True, "message": "停止指令已发送"}


@app.post("/api/reset")
async def reset_monitor():
    """重置状态"""
    state.stop()
    time.sleep(0.5)  # 等待任务结束
    state.reset()
    state.add_log("info", "状态已重置")
    return {"success": True}


@app.post("/api/export")
async def export_results():
    """导出结果到 Excel"""
    if not state.results:
        return {"success": False, "message": "没有可导出的结果"}

    # 这里应该调用实际的 Excel 导出功能
    # 暂时返回模拟响应
    filename = f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    os.makedirs(state.config.output_dir, exist_ok=True)
    file_path = os.path.join(state.config.output_dir, filename)

    state.add_log("info", f"正在导出结果到 Excel...")

    # TODO: 实际的 Excel 导出
    # from openpyxl import Workbook
    # wb = Workbook()
    # ...

    return {
        "success": True,
        "file_path": file_path,
        "filename": filename
    }


@app.get("/api/feishu/test")
async def test_feishu_connection():
    """测试飞书连接"""
    if not FeishuBitableSync:
        return {"success": False, "message": "飞书模块未加载"}

    try:
        feishu = FeishuBitableSync(logger=lambda msg, level: state.add_log(level, msg))
        feishu.update_config({
            "app_id": state.config.feishu_app_id,
            "app_secret": state.config.feishu_app_secret,
            "app_token": state.config.feishu_app_token,
            "table_id": state.config.feishu_table_id
        })

        result = feishu.test_connection()
        state.add_log("success", "飞书连接测试成功")
        return {"success": True, "message": "连接成功"}
    except Exception as e:
        state.add_log("error", f"飞书连接测试失败: {str(e)}")
        return {"success": False, "message": str(e)}


# ============================================================================
# WebSocket 路由
# ============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 端点，用于实时更新"""
    await manager.connect(websocket)

    try:
        # 发送初始状态
        await websocket.send_json({
            "type": "connected",
            "data": {"message": "已连接到服务器"}
        })

        await websocket.send_json(broadcast_status())
        await websocket.send_json(broadcast_progress())

        # 持续监听客户端消息
        while True:
            data = await websocket.receive_json()

            # 处理客户端请求
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

            elif data.get("type") == "get_status":
                await websocket.send_json(broadcast_status())

            elif data.get("type") == "get_logs":
                await websocket.send_json({
                    "type": "logs",
                    "data": {"logs": state.logs[-100:]}
                })

            elif data.get("type") == "get_results":
                await websocket.send_json({
                    "type": "results",
                    "data": {"results": state.results}
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# ============================================================================
# 广播任务（定期向所有客户端推送更新）
# ============================================================================

async def broadcast_updates():
    """定期广播状态更新"""
    while True:
        await asyncio.sleep(1)  # 每秒更新一次

        if manager.active_connections:
            # 广播状态
            await manager.broadcast(broadcast_status())
            await manager.broadcast(broadcast_progress())

            # 广播新日志
            if state.logs:
                await manager.broadcast({
                    "type": "logs",
                    "data": {"logs": state.logs[-10:]}  # 只发送最近10条
                })


# ============================================================================
# 启动事件
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    # 创建必要的目录
    os.makedirs("./uploads", exist_ok=True)
    os.makedirs("./output_v4", exist_ok=True)
    os.makedirs("./logs_v4", exist_ok=True)

    # 启动广播任务
    asyncio.create_task(broadcast_updates())

    print("=" * 50)
    print("小红书链接监测工具 API 已启动")
    print("=" * 50)


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的清理"""
    # 停止运行中的任务
    if state.status == TaskStatus.RUNNING:
        state.stop()
    print("API 服务已关闭")


# ============================================================================
# 主程序入口
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
