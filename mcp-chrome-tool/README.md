# MCP Chrome Tool

一个基于 Model Context Protocol (MCP) 的 Chrome 自动化工具，允许 AI 助手控制浏览器进行各种操作。

## 功能特性

- 🌐 打开网页
- 📸 截图保存
- 🖱️ 点击元素
- ⌨️ 输入文本
- 📄 获取页面标题
- 🚪 关闭浏览器

## 安装步骤

### 1. 安装依赖
```bash
npm install
```

### 2. 运行服务器
```bash
npm start
```

## MCP 配置

将此工具添加到你的 MCP 客户端配置中：

```json
{
  "mcpServers": {
    "chrome-tool": {
      "command": "node",
      "args": ["C:\\Users\\garyt\\OneDrive - insidemedia.net\\GT Mac office\\AI\\linkcheck\\mcp-chrome-tool\\server.js"]
    }
  }
}
```

## 可用工具

### 1. open_url
打开指定的 URL
- **参数**: `url` (字符串) - 要打开的网址

### 2. take_screenshot
截取当前页面截图
- **参数**: `filename` (可选) - 截图文件名

### 3. click_element
点击页面元素
- **参数**: `selector` (字符串) - CSS 选择器

### 4. type_text
在输入框中输入文本
- **参数**:
  - `selector` (字符串) - 输入框的 CSS 选择器
  - `text` (字符串) - 要输入的文本

### 5. get_page_title
获取当前页面标题

### 6. close_browser
关闭浏览器

## 使用示例

1. 打开网页：`https://www.example.com`
2. 截图保存：`example.png`
3. 点击按钮：`.submit-btn`
4. 输入文本：`input[name="search"]`，内容为 "Hello World"

## 技术栈

- Node.js
- Puppeteer (浏览器自动化)
- Model Context Protocol SDK
- Chrome/Chromium

## 注意事项

- 首次运行时会自动下载 Chromium 浏览器
- 建议在有图形界面的环境中运行
- 请确保有足够的系统资源

## 许可证

ISC License