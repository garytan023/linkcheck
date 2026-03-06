"""
WPP MD 小红书链接监测工具 - v3.0 修复版
修复Windows编码问题
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import csv
import os
import threading
import time
import random
from datetime import datetime

class UltimateMonitorV3Fixed:
    def __init__(self, root):
        print("正在初始化v3.0修复版...")
        self.root = root

        # 简化配色，避免Unicode问题
        self.colors = {
            'primary': '#5B6FB5',
            'success': '#34C759',
            'danger': '#FF3B30',
            'bg': '#F8F9FA',
            'card_bg': '#FFFFFF',
            'text_primary': '#2D3748'
        }

        print("正在配置窗口...")
        self.root.title("WPP MD v3.0 Ultimate - 修复版")
        self.root.geometry("900x700")
        self.root.configure(bg=self.colors['bg'])

        # 变量
        self.csv_file = tk.StringVar(value="v3_test_links.csv")
        self.output_dir = tk.StringVar(value="./output_v3_fixed")
        self.is_running = False
        self.stop_flag = False

        # 统计
        self.stats = {
            'total_processed': 0,
            'success_count': 0,
            'failed_count': 0,
            'anti_crawler_count': 0,
            'start_time': None
        }

        print("正在创建界面...")
        self.create_widgets()

        print("v3.0修复版初始化完成")

    def create_widgets(self):
        # 标题区域
        title_frame = tk.Frame(self.root, bg=self.colors['primary'], height=60)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)

        title_label = tk.Label(title_frame, text="WPP MD v3.0 Ultimate - 修复版",
                              font=('Microsoft YaHei UI', 16, 'bold'),
                              bg=self.colors['primary'], fg=self.colors['card_bg'])
        title_label.pack(pady=15)

        # 主容器
        main_container = tk.Frame(self.root, bg=self.colors['bg'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 配置区域
        config_frame = tk.Frame(main_container, bg=self.colors['card_bg'], relief=tk.RAISED, borderwidth=1)
        config_frame.pack(fill=tk.X, pady=(0, 15))

        # CSV文件选择
        csv_frame = tk.Frame(config_frame, bg=self.colors['card_bg'])
        csv_frame.pack(fill=tk.X, padx=15, pady=10)

        tk.Label(csv_frame, text="CSV文件:", font=('Microsoft YaHei UI', 10, 'bold'),
                bg=self.colors['card_bg'], fg=self.colors['text_primary']).pack(side=tk.LEFT)

        csv_entry = tk.Entry(csv_frame, textvariable=self.csv_file, font=('Consolas', 10),
                            bg=self.colors['bg'], fg=self.colors['text_primary'])
        csv_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 10))

        tk.Button(csv_frame, text="浏览", command=self.browse_csv,
                 font=('Microsoft YaHei UI', 9), bg=self.colors['primary'], fg=self.colors['card_bg'],
                 relief=tk.FLAT, padx=15, pady=5).pack(side=tk.RIGHT)

        # 输出目录
        output_frame = tk.Frame(config_frame, bg=self.colors['card_bg'])
        output_frame.pack(fill=tk.X, padx=15, pady=10)

        tk.Label(output_frame, text="输出目录:", font=('Microsoft YaHei UI', 10, 'bold'),
                bg=self.colors['card_bg'], fg=self.colors['text_primary']).pack(side=tk.LEFT)

        output_entry = tk.Entry(output_frame, textvariable=self.output_dir, font=('Consolas', 10),
                               bg=self.colors['bg'], fg=self.colors['text_primary'])
        output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 10))

        tk.Button(output_frame, text="浏览", command=self.browse_output,
                 font=('Microsoft YaHei UI', 9), bg=self.colors['primary'], fg=self.colors['card_bg'],
                 relief=tk.FLAT, padx=15, pady=5).pack(side=tk.RIGHT)

        # 控制按钮
        control_frame = tk.Frame(main_container, bg=self.colors['bg'])
        control_frame.pack(fill=tk.X, pady=15)

        self.start_button = tk.Button(control_frame, text="▶ 开始监测", command=self.start_monitoring,
                                     font=('Microsoft YaHei UI', 12, 'bold'),
                                     bg=self.colors['success'], fg=self.colors['card_bg'],
                                     relief=tk.FLAT, padx=25, pady=10)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = tk.Button(control_frame, text="■ 停止", command=self.stop_monitoring,
                                    font=('Microsoft YaHei UI', 12, 'bold'),
                                    bg=self.colors['danger'], fg=self.colors['card_bg'],
                                    relief=tk.FLAT, padx=20, pady=10, state='disabled')
        self.stop_button.pack(side=tk.LEFT, padx=5)

        # 进度条
        progress_frame = tk.Frame(main_container, bg=self.colors['card_bg'], relief=tk.RAISED, borderwidth=1)
        progress_frame.pack(fill=tk.X, pady=(0, 15))

        self.progress = ttk.Progressbar(progress_frame, mode='determinate', length=600)
        self.progress.pack(fill=tk.X, padx=15, pady=15)

        self.progress_label = tk.Label(progress_frame, text="就绪 - v3.0修复版",
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
            ('anti', '反爬次数:', '0'),
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

        # 日志区域
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

        self.log("v3.0修复版已启动", 'info')
        self.log("修复了Windows控制台编码问题", 'info')

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
        prefixes = {'info': '[信息]', 'success': '[成功]', 'warning': '[警告]', 'error': '[错误]'}
        prefix = prefixes.get(level, '[信息]')

        log_message = f"[{timestamp}] {prefix} {message}\n"

        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

        self.root.update_idletasks()

    def update_stats(self):
        # 键映射关系
        key_mapping = {
            'total': 'total_processed',
            'success': 'success_count',
            'failed': 'failed_count',
            'anti': 'anti_crawler_count'
        }

        for display_key, label in self.stats_labels.items():
            stats_key = key_mapping.get(display_key, display_key)
            value = str(self.stats.get(stats_key, 0))
            label.config(text=value)

            if display_key == 'success' and self.stats[stats_key] > 0:
                label.config(fg=self.colors['success'])
            elif display_key == 'failed' and self.stats[stats_key] > 0:
                label.config(fg=self.colors['danger'])
            elif display_key == 'anti' and self.stats[stats_key] > 0:
                label.config(fg='#FF9500')

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

    def simulate_monitoring(self, items):
        """模拟监测过程"""
        results = []
        self.log("开始模拟v3.0监测流程...", 'info')

        for idx, item in enumerate(items, 1):
            if self.stop_flag:
                self.log("用户中断监测", 'info')
                break

            link = item.get('链接', '')
            self.update_progress(idx, len(items), f"处理链接 {idx}")
            self.log(f"[{idx}/{len(items)}] 处理: {link[:50]}...", 'info')

            # 模拟v3.0随机延迟 (5-12秒的快速版本)
            delay = random.uniform(2, 5)
            self.log(f"等待 {delay:.1f}秒...", 'info')
            time.sleep(delay)

            # 模拟反爬检测
            is_blocked = random.random() < 0.2  # 20%概率
            if is_blocked:
                self.stats['anti_crawler_count'] += 1
                self.log("检测到反爬机制，应用应对策略", 'warning')
                extra_delay = random.uniform(3, 6)
                time.sleep(extra_delay)
                self.update_stats()

            # 模拟处理结果
            success = random.random() > 0.1  # 90%成功率

            if success:
                self.log("处理成功", 'success')
                self.stats['success_count'] += 1
                status = '成功'
                error_msg = ''
            else:
                self.log("处理失败", 'error')
                self.stats['failed_count'] += 1
                status = '失败'
                error_msg = '模拟处理失败'

            result = {
                '序号': item.get('序号', str(idx)),
                '产品': item.get('产品', ''),
                '链接': link,
                '采集状态': status,
                '错误信息': error_msg,
                '检测时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            results.append(result)
            self.stats['total_processed'] += 1
            self.update_stats()

        return results

    def create_report(self, results, output_dir):
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(output_dir, f'v3_修复版报告_{timestamp}.csv')

        try:
            with open(report_file, 'w', newline='', encoding='utf-8-sig') as f:
                fieldnames = ['序号', '产品', '链接', '采集状态', '错误信息', '检测时间']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(results)

            self.log(f"报告已生成: {os.path.basename(report_file)}", 'success')
            return report_file

        except Exception as e:
            self.log(f"生成报告失败: {e}", 'error')
            return None

    def monitoring_task(self):
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
                'anti_crawler_count': 0,
                'start_time': datetime.now()
            }
            self.update_stats()

            csv_file = self.csv_file.get()
            if not os.path.exists(csv_file):
                messagebox.showerror("错误", f"CSV文件不存在: {csv_file}")
                return

            output_dir = self.output_dir.get()

            self.log("="*50)
            self.log("v3.0修复版开始监测", 'info')
            self.log(f"输入: {csv_file}", 'info')
            self.log(f"输出: {output_dir}", 'info')
            self.log("="*50)

            items = self.read_links_from_csv(csv_file)
            self.log(f"读取到 {len(items)} 个链接", 'info')

            if not items:
                messagebox.showwarning("警告", "CSV中没有链接")
                return

            # 执行模拟监测
            results = self.simulate_monitoring(items)

            if not self.stop_flag:
                report_file = self.create_report(results, output_dir)

                # 计算耗时
                total_time = datetime.now() - self.stats['start_time']
                minutes, seconds = divmod(total_time.total_seconds(), 60)

                self.log("="*50)
                self.log("v3.0修复版监测完成！", 'success')
                self.log(f"统计: 总计{len(results)} | 成功{self.stats['success_count']} | 失败{self.stats['failed_count']}", 'info')
                self.log(f"反爬触发: {self.stats['anti_crawler_count']} 次", 'info')
                self.log(f"耗时: {int(minutes)}分{int(seconds)}秒", 'info')
                if report_file:
                    self.log(f"报告: {os.path.basename(report_file)}", 'success')
                self.log("="*50)

                messagebox.showinfo(
                    "监测完成",
                    f"v3.0修复版监测完成！\n\n"
                    f"总计: {len(results)} 条\n"
                    f"成功: {self.stats['success_count']} 条\n"
                    f"失败: {self.stats['failed_count']} 条\n"
                    f"反爬: {self.stats['anti_crawler_count']} 次\n"
                    f"耗时: {int(minutes)}分{int(seconds)}秒"
                )

        except Exception as e:
            self.log(f"监测执行失败: {str(e)}", 'error')
            messagebox.showerror("错误", f"监测失败:\n{str(e)}")

        finally:
            self.is_running = False
            self.start_button.config(state='normal')
            self.stop_button.config(state='disabled')
            self.update_progress(0, 1, "就绪")

    def start_monitoring(self):
        if not self.is_running:
            thread = threading.Thread(target=self.monitoring_task, daemon=True)
            thread.start()

    def stop_monitoring(self):
        if self.is_running:
            self.stop_flag = True
            self.log("正在停止监测...", 'warning')

def main():
    print("正在启动WPP MD v3.0 Ultimate修复版...")

    try:
        root = tk.Tk()

        # 设置窗口位置
        root.update_idletasks()
        width = 900
        height = 700
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry(f'{width}x{height}+{x}+{y}')

        app = UltimateMonitorV3Fixed(root)
        print("应用程序启动成功")
        root.mainloop()

    except Exception as e:
        print(f"启动失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()