#!/usr/bin/env node

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const { CallToolRequestSchema, ListToolsRequestSchema } = require('@modelcontextprotocol/sdk/types.js');
const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

class MCPChromeServer {
    constructor() {
        this.server = new Server({
            name: 'mcp-chrome-tool',
            version: '1.0.0',
        }, {
            capabilities: {
                tools: {},
            },
        });

        this.browser = null;
        this.page = null;
        this.apiKey = process.env.PRIMARY_API_KEY || null;
        this.setupToolHandlers();
    }

    async setupBrowser() {
        if (!this.browser) {
            this.browser = await puppeteer.launch({
                headless: false,
                defaultViewport: { width: 1280, height: 720 },
                args: ['--no-sandbox', '--disable-setuid-sandbox']
            });
            this.page = await this.browser.newPage();

            // 设置页面超时和错误处理
            this.page.setDefaultTimeout(30000);
            this.page.setDefaultNavigationTimeout(30000);
        }
    }

    setupToolHandlers() {
        this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
            tools: [
                {
                    name: 'open_url',
                    description: 'Open a URL in Chrome browser',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            url: {
                                type: 'string',
                                description: 'URL to open'
                            }
                        },
                        required: ['url']
                    }
                },
                {
                    name: 'take_screenshot',
                    description: 'Take a screenshot of the current page',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            filename: {
                                type: 'string',
                                description: 'Filename for the screenshot (optional)'
                            }
                        }
                    }
                },
                {
                    name: 'click_element',
                    description: 'Click an element on the page',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            selector: {
                                type: 'string',
                                description: 'CSS selector of the element to click'
                            }
                        },
                        required: ['selector']
                    }
                },
                {
                    name: 'type_text',
                    description: 'Type text into an input field',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            selector: {
                                type: 'string',
                                description: 'CSS selector of the input field'
                            },
                            text: {
                                type: 'string',
                                description: 'Text to type'
                            }
                        },
                        required: ['selector', 'text']
                    }
                },
                {
                    name: 'get_page_title',
                    description: 'Get the title of the current page',
                    inputSchema: {
                        type: 'object',
                        properties: {}
                    }
                },
                {
                    name: 'close_browser',
                    description: 'Close the browser',
                    inputSchema: {
                        type: 'object',
                        properties: {}
                    }
                },
                {
                    name: 'test_links_from_file',
                    description: 'Test multiple links from a text file and take screenshots',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            filepath: {
                                type: 'string',
                                description: 'Path to the text file containing URLs (one per line)'
                            },
                            output_dir: {
                                type: 'string',
                                description: 'Directory to save screenshots (optional, defaults to "screenshots")'
                            }
                        },
                        required: ['filepath']
                    }
                },
                {
                    name: 'verify_api_key',
                    description: 'Verify if API key is configured',
                    inputSchema: {
                        type: 'object',
                        properties: {}
                    }
                }
            ]
        }));

        this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
            const { name, arguments: args } = request.params;

            try {
                switch (name) {
                    case 'open_url':
                        await this.setupBrowser();
                        await this.page.goto(args.url);
                        return {
                            content: [{ type: 'text', text: `Successfully opened ${args.url}` }]
                        };

                    case 'take_screenshot':
                        if (!this.page) {
                            throw new Error('No page is open. Please open a URL first.');
                        }
                        const filename = args.filename || `screenshot_${Date.now()}.png`;
                        await this.page.screenshot({
                            path: filename,
                            fullPage: true
                        });
                        return {
                            content: [{ type: 'text', text: `Screenshot saved as ${filename}` }]
                        };

                    case 'click_element':
                        if (!this.page) {
                            throw new Error('No page is open. Please open a URL first.');
                        }
                        await this.page.waitForSelector(args.selector, { timeout: 5000 });
                        await this.page.click(args.selector);
                        return {
                            content: [{ type: 'text', text: `Successfully clicked element: ${args.selector}` }]
                        };

                    case 'type_text':
                        if (!this.page) {
                            throw new Error('No page is open. Please open a URL first.');
                        }
                        await this.page.waitForSelector(args.selector, { timeout: 5000 });
                        await this.page.type(args.selector, args.text);
                        return {
                            content: [{ type: 'text', text: `Successfully typed text into: ${args.selector}` }]
                        };

                    case 'get_page_title':
                        if (!this.page) {
                            throw new Error('No page is open. Please open a URL first.');
                        }
                        const title = await this.page.title();
                        return {
                            content: [{ type: 'text', text: `Page title: ${title}` }]
                        };

                    case 'close_browser':
                        if (this.browser) {
                            await this.browser.close();
                            this.browser = null;
                            this.page = null;
                            return {
                                content: [{ type: 'text', text: 'Browser closed successfully' }]
                            };
                        } else {
                            return {
                                content: [{ type: 'text', text: 'No browser is currently open' }]
                            };
                        }

                    case 'test_links_from_file':
                        await this.setupBrowser();
                        const outputDir = args.output_dir || 'screenshots';

                        // 创建输出目录
                        if (!fs.existsSync(outputDir)) {
                            fs.mkdirSync(outputDir, { recursive: true });
                        }

                        // 读取链接文件
                        const links = fs.readFileSync(args.filepath, 'utf8')
                            .split('\n')
                            .map(line => line.trim())
                            .filter(line => line && line.startsWith('http'));

                        const results = [];

                        for (let i = 0; i < links.length; i++) {
                            const url = links[i];
                            try {
                                console.error(`Processing link ${i + 1}/${links.length}: ${url}`);

                                // 为每个链接创建新页面以避免 Frame 分离问题
                                const page = await this.browser.newPage();

                                // 访问链接
                                await page.goto(url, {
                                    waitUntil: 'networkidle2',
                                    timeout: 30000
                                });

                                // 等待页面加载 - 使用不同的方法
                                await new Promise(resolve => setTimeout(resolve, 3000));

                                // 生成截图文件名
                                const screenshotName = `link_${i + 1}_${Date.now()}.png`;
                                const screenshotPath = path.join(outputDir, screenshotName);

                                // 截图
                                await page.screenshot({
                                    path: screenshotPath,
                                    fullPage: true
                                });

                                // 获取页面标题
                                const title = await page.title();

                                results.push({
                                    link: url,
                                    status: 'success',
                                    title: title,
                                    screenshot: screenshotPath
                                });

                                console.error(`✓ Successfully processed: ${url}`);

                                // 关闭页面
                                await page.close();

                            } catch (error) {
                                results.push({
                                    link: url,
                                    status: 'error',
                                    error: error.message
                                });
                                console.error(`✗ Error processing ${url}: ${error.message}`);
                            }
                        }

                        // 保存结果报告
                        const reportPath = path.join(outputDir, `test_report_${Date.now()}.json`);
                        fs.writeFileSync(reportPath, JSON.stringify(results, null, 2));

                        return {
                            content: [{
                                type: 'text',
                                text: `Testing completed!\n\nProcessed ${links.length} links.\nSuccessful: ${results.filter(r => r.status === 'success').length}\nFailed: ${results.filter(r => r.status === 'error').length}\n\nScreenshots saved in: ${outputDir}\nReport saved as: ${reportPath}`
                            }]
                        };

                    case 'verify_api_key':
                        if (this.apiKey) {
                            return {
                                content: [{ type: 'text', text: `API key is configured: ${this.apiKey.substring(0, 3)}***` }]
                            };
                        } else {
                            return {
                                content: [{ type: 'text', text: 'API key is not configured' }],
                                isError: true
                            };
                        }

                    default:
                        throw new Error(`Unknown tool: ${name}`);
                }
            } catch (error) {
                return {
                    content: [{ type: 'text', text: `Error: ${error.message}` }],
                    isError: true
                };
            }
        });
    }

    async run() {
        const transport = new StdioServerTransport();
        await this.server.connect(transport);
        console.error('MCP Chrome Tool server running on stdio');
    }

    async cleanup() {
        if (this.browser) {
            await this.browser.close();
        }
    }
}

const server = new MCPChromeServer();

// Handle graceful shutdown
process.on('SIGINT', async () => {
    console.error('\nShutting down gracefully...');
    await server.cleanup();
    process.exit(0);
});

process.on('SIGTERM', async () => {
    console.error('\nShutting down gracefully...');
    await server.cleanup();
    process.exit(0);
});

server.run().catch(console.error);