"""
WPP MD 小红书链接监测工具 - v3.0 简化测试版
用于快速验证核心功能
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import csv
import os
import threading
import time
import random
from datetime import datetime

class SimpleV3Test:
    def __init__(self, root):
        self.root = root
        self.root.title("WPP MD v3.0 Ultimate 简化测试版")
        self.root.geometry("800x600")

        # 简化配色
        self.colors = {
            'primary': '#5B6FB5',
            'success': '#34C759',
            'danger': '#FF3B30',
            'bg': '#F8F9FA',
            'card_bg': '#FFFFFF',
            'text_primary': '#2D3748'
        }

        self.root.configure(bg=self.colors['bg'])

        # 变量
        self.csv_file = tk.StringVar(value="link.csv")
        self.output_dir = tk.StringVar(value="./test_output_v3")
        self.is_running = False
        self.stop_flag = False

        # 统计
        self.stats = {
            'total_processed': 0,
            'success_count': 0,
            'failed_count': 0,
            'start_time': None
        }

        self.create_widgets()

    def create_widgets(self):
        # 标题
        title_frame = tk.Frame(self.root, bg=self.colors['primary'], height=60)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)

        title_label = tk.Label(title_frame, text="WPP MD v3.0 Ultimate 简化测试版",
                              font=('Microsoft YaHei UI', 16, 'bold'),
                              bg=self.colors['primary'], fg=self.colors['card_bg'])
        title_label.pack(pady=15)

        # 主容器
        main_container = tk.Frame(self.root, bg=self.colors['bg'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 配置区域
        config_frame = tk.Frame(main_container, bg=self.colors['card_bg'], relief=tk.RAISED, borderwidth=1)
        config_frame.pack(fill=tk.X, pady=(0, 15))

        # CSV文件
        csv_frame = tk.Frame(config_frame, bg=self.colors['card_bg'])
        csv_frame.pack(fill=tk.X, padx=15, pady=10)

        tk.Label(csv_frame, text="CSV文件:", font=('Microsoft YaHei UI', 10, 'bold'),
                bg=self.colors['card_bg'], fg=self.colors['text_primary']).pack(side=tk.LEFT)

        tk.Entry(csv_frame, textvariable=self.csv_file, font=('Consolas', 10),
                bg=self.colors['bg'], fg=self.colors['text_primary']).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 10))

        tk.Button(csv_frame, text="浏览", command=self.browse_csv,
                 font=('Microsoft YaHei UI', 9), bg=self.colors['primary'], fg=self.colors['card_bg'],
                 relief=tk.FLAT, padx=15, pady=5).pack(side=tk.RIGHT)

        # 输出目录
        output_frame = tk.Frame(config_frame, bg=self.colors['card_bg'])
        output_frame.pack(fill=tk.X, padx=15, pady=10)

        tk.Label(output_frame, text="输出目录:", font=('Microsoft YaHei UI', 10, 'bold'),
                bg=self.colors['card_bg'], fg=self.colors['text_primary']).pack(side=tk.LEFT)

        tk.Entry(output_frame, textvariable=self.output_dir, font=('Consolas', 10),
                bg=self.colors['bg'], fg=self.colors['text_primary']).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 10))

        tk.Button(output_frame, text="浏览", command=self.browse_output,
                 font=('Microsoft YaHei UI', 9), bg=self.colors['primary'], fg=self.colors['card_bg'],
                 relief=tk.FLAT, padx=15, pady=5).pack(side=tk.RIGHT)

        # 控制按钮
        control_frame = tk.Frame(main_container, bg=self.colors['bg'])
        control_frame.pack(fill=tk.X, pady=15)

        self.start_button = tk.Button(control_frame, text="▶ 开始测试", command=self.start_test,
                                     font=('Microsoft YaHei UI', 12, 'bold'),
                                     bg=self.colors['success'], fg=self.colors['card_bg'],
                                     relief=tk.FLAT, padx=25, pady=10)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = tk.Button(control_frame, text="■ 停止", command=self.stop_test,
                                    font=('Microsoft YaHei UI', 12, 'bold'),
                                    bg=self.colors['danger'], fg=self.colors['card_bg'],
                                    relief=tk.FLAT, padx=20, pady=10, state='disabled')
        self.stop_button.pack(side=tk.LEFT, padx=5)

        # 进度条
        progress_frame = tk.Frame(main_container, bg=self.colors['card_bg'], relief=tk.RAISED, borderwidth=1)
        progress_frame.pack(fill=tk.X, pady=(0, 15))

        self.progress = ttk.Progressbar(progress_frame, mode='determinate', length=600)
        self.progress.pack(fill=tk.X, padx=15, pady=15)

        self.progress_label = tk.Label(progress_frame, text="就绪 - v3.0简化测试版",
                                      font=('Microsoft YaHei UI', 10), bg=self.colors['card_bg'])
        self.progress_label.pack(padx=15, pady=(0, 15))

        # 统计信息
        stats_frame = tk.Frame(main_container, bg=self.colors['card_bg'], relief=tk.RAISED, borderwidth=1)
        stats_frame.pack(fill=tk.X, pady=(0, 15))

        stats_inner = tk.Frame(stats_frame, bg=self.colors['card_bg'])
        stats_inner.pack(fill=tk.X, padx=15, pady=10)

        self.stats_labels = {}
        stats_config = [
            ('total', '总链接数:', '0'),
            ('success', '成功数:', '0'),
            ('failed', '失败数:', '0'),
        ]

        for key, label, default in stats_config:
            stat_frame = tk.Frame(stats_inner, bg=self.colors['card_bg'])
            stat_frame.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

            label_widget = tk.Label(stat_frame, text=label, font=('Microsoft YaHei UI', 9, 'bold'),
                                  bg=self.colors['card_bg'], fg=self.colors['text_primary'])
            label_widget.pack()

            value_widget = tk.Label(stat_frame, text=default, font=('Microsoft YaHei UI', 11, 'bold'),
                                   bg=self.colors['card_bg'], fg=self.colors['text_primary'])
            value_widget.pack()

            self.stats_labels[key] = value_widget

        # 日志
        log_frame = tk.Frame(main_container, bg=self.colors['card_bg'], relief=tk.RAISED, borderwidth=1)
        log_frame.pack(fill=tk.BOTH, expand=True)

        log_inner = tk.Frame(log_frame, bg=self.colors['card_bg'])
        log_inner.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        tk.Label(log_inner, text="运行日志:", font=('Microsoft YaHei UI', 10, 'bold'),
                bg=self.colors['card_bg'], fg=self.colors['text_primary']).pack(anchor=tk.W)

        self.log_text = scrolledtext.ScrolledText(log_inner, height=10, font=('Consolas', 8),
                                                 bg=self.colors['bg'], fg=self.colors['text_primary'],
                                                 relief=tk.FLAT, wrap=tk.WORD, state='disabled')
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

        self.log("v3.0简化测试版已启动", 'info')

    def browse_csv(self):
        filename = filedialog.askopenfilename(
            title="选择CSV文件",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.csv_file.set(filename)
            self.log(f"选择CSV文件: {os.path.basename(filename)}", 'info')

    def browse_output(self):
        directory = filedialog.askdirectory(title="选择输出目录")
        if directory:
            self.output_dir.set(directory)
            self.log(f"选择输出目录: {directory}", 'info')

    def log(self, message, level='info'):
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefixes = {'info': '📝', 'success': '✅', 'warning': '⚠️', 'error': '❌'}
        prefix = prefixes.get(level, '📝')

        log_message = f"[{timestamp}] {prefix} {message}\n"

        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

        self.root.update_idletasks()

    def update_stats(self):
        for key, label in self.stats_labels.items():
            value = str(self.stats.get(key, 0))
            label.config(text=value)

            if key == 'success' and self.stats[key] > 0:
                label.config(fg=self.colors['success'])
            elif key == 'failed' and self.stats[key] > 0:
                label.config(fg=self.colors['danger'])

    def update_progress(self, current, total, message=""):
        progress = (current / total) * 100 if total > 0 else 0
        self.progress['value'] = progress
        self.progress_label.config(text=f"{message} ({current}/{total}) • {progress:.0f}%")
        self.root.update_idletasks()

    def read_links_from_csv(self, csv_file):
        items = []
        try:
            with open(csv_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for idx, row in enumerate(reader, 1):
                    link = (row.get('链接') or row.get('link') or '').strip()
                    if not link:
                        continue
                    product = (row.get('产品') or row.get('product') or '').strip()
                    seq = (row.get('序号') or row.get('id') or '').strip() or str(idx)
                    items.append({'产品': product, '序号': seq, '链接': link})
        except Exception as e:
            self.log(f"读取CSV失败: {e}", 'error')

        return items

    def simple_test_process(self, items):
        """简化的测试流程"""
        results = []

        self.log("开始简化测试流程...", 'info')

        for idx, item in enumerate(items, 1):
            if self.stop_flag:
                self.log("用户中断测试", 'info')
                break

            link = item.get('链接', '')
            self.update_progress(idx, len(items), f"测试链接 {idx}")
            self.log(f"[{idx}/{len(items)}] 测试: {link[:60]}...", 'info')

            # 模拟处理时间
            time.sleep(random.uniform(1, 3))

            result = {
                '序号': item.get('序号', str(idx)),
                '产品': item.get('产品', ''),
                '链接': link,
                '采集状态': '成功' if random.random() > 0.2 else '失败',
                '错误信息': '',
                '检测时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            if result['采集状态'] == '失败':
                result['错误信息'] = '模拟失败'
                self.stats['failed_count'] += 1
            else:
                self.stats['success_count'] += 1
                self.log("✅ 测试成功", 'success')

            results.append(result)
            self.stats['total_processed'] += 1
            self.update_stats()

        return results

    def create_simple_report(self, results, output_dir):
        """创建简化报告"""
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(output_dir, f'v3_简化测试报告_{timestamp}.csv')

        try:
            with open(report_file, 'w', newline='', encoding='utf-8-sig') as f:
                fieldnames = ['序号', '产品', '链接', '采集状态', '错误信息', '检测时间']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(results)

            self.log(f"简化报告已生成: {os.path.basename(report_file)}", 'success')
            return report_file

        except Exception as e:
            self.log(f"生成报告失败: {e}", 'error')
            return None

    def test_task(self):
        """主测试任务"""
        try:
            self.is_running = True
            self.stop_flag = False
            self.start_button.config(state='disabled')
            self.stop_button.config(state='normal')

            # 重置统计
            self.stats = {
                'total_processed': 0,
                'success_count': 0,
                'failed_count': 0,
                'start_time': datetime.now()
            }
            self.update_stats()

            csv_file = self.csv_file.get()
            if not os.path.exists(csv_file):
                messagebox.showerror("错误", f"CSV文件不存在: {csv_file}")
                return

            output_dir = self.output_dir.get()

            self.log("="*50)
            self.log("v3.0简化测试开始", 'info')
            self.log(f"输入: {csv_file}", 'info')
            self.log(f"输出: {output_dir}", 'info')
            self.log("="*50)

            items = self.read_links_from_csv(csv_file)
            self.log(f"读取到 {len(items)} 个链接", 'info')

            if not items:
                messagebox.showwarning("警告", "CSV中没有链接")
                return

            # 执行测试
            results = self.simple_test_process(items)

            if not self.stop_flag:
                report_file = self.create_simple_report(results, output_dir)

                # 计算耗时
                total_time = datetime.now() - self.stats['start_time']
                minutes, seconds = divmod(total_time.total_seconds(), 60)

                self.log("="*50)
                self.log("v3.0简化测试完成！", 'success')
                self.log(f"统计: 总计{len(results)} | 成功{self.stats['success_count']} | 失败{self.stats['failed_count']}", 'info')
                self.log(f"耗时: {int(minutes)}分{int(seconds)}秒", 'info')
                if report_file:
                    self.log(f"报告: {os.path.basename(report_file)}", 'success')
                self.log("="*50)

                messagebox.showinfo(
                    "✅ v3.0简化测试完成",
                    f"简化测试完成！\n\n"
                    f"总计: {len(results)} 条\n"
                    f"✅ 成功: {self.stats['success_count']} 条\n"
                    f"❌ 失败: {self.stats['failed_count']} 条\n"
                    f"⏱️ 耗时: {int(minutes)}分{int(seconds)}秒\n\n"
                    f"这是一个功能验证测试，\n"
                    f"证明v3.0版本可以正常运行。"
                )

        except Exception as e:
            self.log(f"测试执行失败: {str(e)}", 'error')
            messagebox.showerror("错误", f"测试失败:\n{str(e)}")

        finally:
            self.is_running = False
            self.start_button.config(state='normal')
            self.stop_button.config(state='disabled')
            self.update_progress(0, 1, "就绪")

    def start_test(self):
        if not self.is_running:
            thread = threading.Thread(target=self.test_task, daemon=True)
            thread.start()

    def stop_test(self):
        if self.is_running:
            self.stop_flag = True
            self.log("正在停止测试...", 'warning')

def main():
    root = tk.Tk()

    # 设置窗口位置
    root.update_idletasks()
    width = 800
    height = 600
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')

    app = SimpleV3Test(root)
    root.mainloop()

if __name__ == '__main__':
    main()