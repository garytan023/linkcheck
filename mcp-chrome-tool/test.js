// Test script for MCP Chrome Tool
// This script demonstrates how to use the MCP Chrome Tool

const { spawn } = require('child_process');

console.log('🚀 Starting MCP Chrome Tool test...');

// Start the MCP server
const mcpServer = spawn('C:\\Program Files\\nodejs\\node.exe', ['server.js'], {
    cwd: './mcp-chrome-tool',
    stdio: ['pipe', 'pipe', 'inherit']
});

// Send a list tools request
const listToolsRequest = {
    jsonrpc: '2.0',
    method: 'tools/list',
    id: 1
};

mcpServer.stdin.write(JSON.stringify(listToolsRequest) + '\n');

let responseBuffer = '';

mcpServer.stdout.on('data', (data) => {
    responseBuffer += data.toString();

    // Try to parse complete JSON responses
    const lines = responseBuffer.split('\n');
    for (let i = 0; i < lines.length - 1; i++) {
        if (lines[i].trim()) {
            try {
                const response = JSON.parse(lines[i].trim());
                console.log('📋 MCP Response:', JSON.stringify(response, null, 2));

                if (response.id === 1 && response.result) {
                    console.log('✅ Available tools:');
                    response.result.tools.forEach(tool => {
                        console.log(`  - ${tool.name}: ${tool.description}`);
                    });

                    // Close the server after getting tools list
                    setTimeout(() => {
                        console.log('🔧 Test completed successfully!');
                        mcpServer.kill();
                    }, 1000);
                }
            } catch (error) {
                // Skip invalid JSON lines
            }
        }
    }
    responseBuffer = lines[lines.length - 1]; // Keep incomplete line
});

mcpServer.on('close', (code) => {
    console.log(`🏁 MCP server exited with code ${code}`);
});

mcpServer.on('error', (error) => {
    console.error('❌ Error starting MCP server:', error);
});