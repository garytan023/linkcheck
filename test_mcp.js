#!/usr/bin/env node

const { spawn } = require('child_process');
const path = require('path');

// 启动 MCP 服务器
const serverPath = path.join(__dirname, 'mcp-chrome-tool', 'server.js');
const serverProcess = spawn('node', [serverPath], {
    env: { ...process.env, PRIMARY_API_KEY: 'key' },
    stdio: ['pipe', 'pipe', 'inherit']
});

let requestId = 1;

function sendRequest(method, params = {}) {
    const request = {
        jsonrpc: '2.0',
        id: requestId++,
        method: method,
        params: params
    };

    serverProcess.stdin.write(JSON.stringify(request) + '\n');
}

// 监听响应
serverProcess.stdout.on('data', (data) => {
    const lines = data.toString().trim().split('\n');
    lines.forEach(line => {
        if (line.trim()) {
            try {
                const response = JSON.parse(line);
                console.log('Response:', JSON.stringify(response, null, 2));
            } catch (e) {
                console.log('Raw output:', line);
            }
        }
    });
});

// 测试流程
setTimeout(() => {
    console.log('1. 验证 API 密钥...');
    sendRequest('tools/call', {
        name: 'verify_api_key',
        arguments: {}
    });
}, 1000);

setTimeout(() => {
    console.log('\n2. 测试批量链接处理...');
    sendRequest('tools/call', {
        name: 'test_links_from_file',
        arguments: {
            filepath: path.join(__dirname, 'links.txt'),
            output_dir: path.join(__dirname, 'mcp_screenshots')
        }
    });
}, 3000);

setTimeout(() => {
    console.log('\n3. 关闭浏览器...');
    sendRequest('tools/call', {
        name: 'close_browser',
        arguments: {}
    });

    // 关闭服务器
    setTimeout(() => {
        serverProcess.kill();
        process.exit(0);
    }, 2000);
}, 30000); // 给链接测试30秒时间

serverProcess.on('error', (error) => {
    console.error('Server error:', error);
});

serverProcess.on('close', (code) => {
    console.log(`Server process exited with code ${code}`);
});