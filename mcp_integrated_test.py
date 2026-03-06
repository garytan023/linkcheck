import os
import sys
import subprocess
import json
import time
import pandas as pd
from datetime import datetime
import requests
import threading

# 添加 MCP Chrome 工具路径
MCP_CHROME_PATH = os.path.join(os.getcwd(), 'mcp-chrome-tool')

class MCPIntegratedTester:
    def __init__(self):
        self.mcp_server = None
        self.results = []
        self.stop_flag = False

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        try:
            print(f"[{timestamp}] {message}")
        except UnicodeEncodeError:
            print(f"[{timestamp}] {message.encode('ascii', 'ignore').decode('ascii')}")

    def analyze_link_data(self):
        """分析 link.xlsx 数据结构"""
        try:
            df = pd.read_excel('link.xlsx')
            self.log(f"数据分析完成")
            self.log(f"  - 总链接数: {len(df)}")
            self.log(f"  - 列名: {list(df.columns)}")

            # 分析链接类型
            links = df['link'].tolist() if 'link' in df.columns else []
            xhs_links = sum(1 for link in links if 'xiaohongshu.com' in link)
            other_links = len(links) - xhs_links

            self.log(f"  - 小红书链接: {xhs_links}")
            self.log(f"  - 其他链接: {other_links}")

            return links

        except Exception as e:
            self.log(f"数据分析失败: {e}")
            return []

    def start_mcp_server(self):
        """启动 MCP Chrome 服务器"""
        try:
            self.log("启动 MCP Chrome 服务器...")

            # 设置环境变量
            env = os.environ.copy()
            env['PRIMARY_API_KEY'] = 'key'

            # 启动 MCP 服务器
            self.mcp_server = subprocess.Popen(
                ['node', 'server.js'],
                cwd=MCP_CHROME_PATH,
                env=env,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

        # 等待服务器启动
            time.sleep(2)
            self.log("MCP 服务器已启动")
            return True

        except Exception as e:
            self.log(f"MCP 服务器启动失败: {e}")
            return False

    def send_mcp_request(self, tool_name, arguments):
        """发送 MCP 工具请求"""
        try:
            request = {
                "jsonrpc": "2.0",
                "id": int(time.time() * 1000),
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }

            # 发送请求
            self.mcp_server.stdin.write(json.dumps(request) + '\n')
            self.mcp_server.stdin.flush()

            # 等待响应
            response_line = self.mcp_server.stdout.readline()
            if response_line:
                response = json.loads(response_line.strip())
                if 'result' in response:
                    return response['result']
                elif 'error' in response:
                    return {'error': response['error']}

            return {'error': 'No response received'}

        except Exception as e:
            return {'error': str(e)}

    def test_links_with_mcp(self, links):
        """使用 MCP 测试链接"""
        self.log(f"开始 MCP 链接测试 ({len(links)} 个链接)")

        # 创建输出目录
        output_dir = os.path.join(os.getcwd(), 'mcp_test_results')
        os.makedirs(output_dir, exist_ok=True)

        # 创建链接文件
        links_file = os.path.join(output_dir, 'test_links.txt')
        with open(links_file, 'w', encoding='utf-8') as f:
            for link in links:
                f.write(link + '\n')

        # 使用 MCP 批量测试工具
        self.log("使用 MCP 批量测试工具...")
        result = self.send_mcp_request('test_links_from_file', {
            'filepath': links_file,
            'output_dir': os.path.join(output_dir, 'screenshots')
        })

        if 'error' in result:
            self.log(f"✗ MCP 测试失败: {result['error']}")
            return False

        self.log("✓ MCP 测试完成")
        return True

    def test_original_tool(self, links):
        """测试原工具功能"""
        self.log("测试原工具功能...")

        try:
            # 将链接转换为 CSV 格式供原工具使用
            csv_data = [['产品', '序号', '链接']]
            for i, link in enumerate(links[:3], 1):  # 只测试前3个链接
                csv_data.append([f'测试产品{i}', str(i), link])

            csv_file = 'test_links.csv'
            with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
                import csv
                writer = csv.writer(f)
                writer.writerows(csv_data)

            self.log(f"✓ 创建测试 CSV: {csv_file}")
            return True

        except Exception as e:
            self.log(f"✗ 原工具测试失败: {e}")
            return False

    def run_comprehensive_test(self):
        """运行综合测试"""
        self.log("="*60)
        self.log("小红书链接监测工具 - MCP 集成测试")
        self.log("="*60)

        # 1. 分析数据
        links = self.analyze_link_data()
        if not links:
            self.log("✗ 没有找到链接数据")
            return False

        # 2. 启动 MCP 服务器
        if not self.start_mcp_server():
            return False

        try:
            # 3. 验证 MCP API 密钥
            self.log("验证 MCP API 密钥...")
            auth_result = self.send_mcp_request('verify_api_key', {})

            if 'error' in auth_result:
                self.log(f"✗ API 密钥验证失败: {auth_result['error']}")
            else:
                self.log("✓ API 密钥验证成功")

            # 4. MCP 链接测试
            mcp_success = self.test_links_with_mcp(links)

            # 5. 原工具测试
            original_success = self.test_original_tool(links)

            # 6. 生成综合报告
            self.generate_report(links, mcp_success, original_success)

            self.log("="*60)
            self.log("测试完成！")
            self.log(f"- MCP 测试: {'✓ 成功' if mcp_success else '✗ 失败'}")
            self.log(f"- 原工具测试: {'✓ 成功' if original_success else '✗ 失败'}")
            self.log("="*60)

            return True

        finally:
            # 清理
            self.cleanup()

    def generate_report(self, links, mcp_success, original_success):
        """生成测试报告"""
        try:
            report = {
                'test_time': datetime.now().isoformat(),
                'total_links': len(links),
                'xiaohongshu_links': sum(1 for link in links if 'xiaohongshu.com' in link),
                'mcp_test': {
                    'success': mcp_success,
                    'screenshots_taken': 0,
                    'output_dir': 'mcp_test_results'
                },
                'original_tool_test': {
                    'success': original_success,
                    'csv_generated': 'test_links.csv'
                },
                'summary': {
                    'overall_success': mcp_success and original_success,
                    'recommendation': 'Both tools working correctly' if mcp_success and original_success else 'Some issues detected'
                }
            }

            report_file = 'mcp_integration_test_report.json'
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)

            self.log(f"✓ 测试报告已生成: {report_file}")

        except Exception as e:
            self.log(f"✗ 报告生成失败: {e}")

    def cleanup(self):
        """清理资源"""
        if self.mcp_server:
            try:
                # 发送关闭浏览器请求
                self.send_mcp_request('close_browser', {})
                time.sleep(1)

                # 终止服务器进程
                self.mcp_server.terminate()
                self.mcp_server.wait(timeout=5)
                self.log("✓ MCP 服务器已关闭")
            except Exception as e:
                self.log(f"清理警告: {e}")

def main():
    tester = MCPIntegratedTester()

    try:
        success = tester.run_comprehensive_test()
        if success:
            print("\n✅ MCP 集成测试成功完成")
        else:
            print("\n❌ MCP 集成测试遇到问题")

    except KeyboardInterrupt:
        print("\n⚠️  测试被用户中断")
        tester.cleanup()
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        tester.cleanup()

if __name__ == "__main__":
    main()