#!/usr/bin/env node
const fs = require('fs');
const https = require('https');

// 配置
const RSS_SERVER = 'http://8.138.40.155:9001/feed';
const OPML_FILE = '/Users/garytan/.openclaw/workspace-dev/data/wechat_rss_subscriptions.opml';
const DISCORD_CHANNEL_ID = '1478997781187268608';
const DISCORD_BOT_TOKEN = process.env.DISCORD_BOT_TOKEN || '';
const FEISHU_APP_ID = process.env.FEISHU_APP_ID || '';
const FEISHU_APP_SECRET = process.env.FEISHU_APP_SECRET || '';
const FEISHU_USER_OPENID = 'ou_d635f4f3d20ac474cf8575038b5d2b33';

const { Client } = require('@larksuiteoapi/node-sdk');
const feishu = new Client({ appId: FEISHU_APP_ID, appSecret: FEISHU_APP_SECRET });

async function getFeishuToken() {
  return new Promise((resolve) => {
    const data = JSON.stringify({ app_id: FEISHU_APP_ID, app_secret: FEISHU_APP_SECRET });
    const req = https.request({
      hostname: 'open.feishu.cn', port: 443, path: '/open-apis/auth/v3/tenant_access_token/internal',
      method: 'POST', headers: { 'Content-Type': 'application/json', 'Content-Length': data.length }
    }, (res) => {
      let body = ''; res.on('data', d => body += d); res.on('end', () => {
        try { resolve(JSON.parse(body).tenant_access_token); } catch { resolve(null); }
      });
    });
    req.write(data); req.end();
  });
}

async function createFeishuDoc(title, content) {
  const token = await getFeishuToken();
  // 创建文档
  const docRes = await new Promise((resolve) => {
    const data = JSON.stringify({ document: { parent_node_token: 'root', title } });
    const req = https.request({
      hostname: 'open.feishu.cn', port: 443, path: '/open-apis/docx/v1/documents',
      method: 'POST', headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json', 'Content-Length': data.length }
    }, (res) => { let b = ''; res.on('data', d => b += d); res.on('end', () => resolve(JSON.parse(b))); });
    req.write(data); req.end();
  });
  
  if (docRes.code !== 0) return null;
  const docId = docRes.data.document.document_id;
  
  // 写入内容
  const blocks = content.split('\n\n').map(line => ({
    type: 'paragraph', paragraph: { elements: [{ type: 'textrun', text: line }] }
  }));
  
  await new Promise((resolve) => {
    const data = JSON.stringify({ document: { document_id: docId, blocks } });
    const req = https.request({
      hostname: 'open.feishu.cn', port: 443, path: `/open-apis/docx/v1/documents/${docId}/blocks`,
      method: 'POST', headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json', 'Content-Length': data.length }
    }, (res) => { let b = ''; res.on('data', d => b += d); res.on('end', () => resolve(JSON.parse(b))); });
    req.write(data); req.end();
  });
  
  // 添加权限
  try {
    await feishu.drive.permissionMember.create({
      path: { token: docId },
      params: { type: 'docx', need_notification: false },
      data: { member_type: 'openid', member_id: FEISHU_USER_OPENID, perm: 'full_access' }
    });
    console.log('✅ 权限开放成功');
  } catch(e) { console.log('⚠️ 权限开放失败:', e.message); }
  
  return docId;
}

async function main() {
  console.log('=== 每日资讯同步 (Node.js版) ===');
  // 简化：直接返回已有内容
  const content = `测试文档 - Node.js版本创建成功`;
  const docId = await createFeishuDoc('测试', content);
  if (docId) console.log(`✅ 文档: https://open.feishu.cn/document/${docId}`);
}

main();
