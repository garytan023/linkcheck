#!/bin/bash
DOC_ID=$1
CONTENT="$2"

FEISHU_APP_ID=${FEISHU_APP_ID:-}
FEISHU_APP_SECRET=${FEISHU_APP_SECRET:-}

if [ -z "$FEISHU_APP_ID" ] || [ -z "$FEISHU_APP_SECRET" ]; then
  echo "错误: 缺少环境变量 FEISHU_APP_ID 或 FEISHU_APP_SECRET" >&2
  exit 1
fi

# 先获取用户token
TOKEN=$(curl -s -X POST "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal" \
  -H "Content-Type: application/json" \
  -d "{\"app_id\": \"$FEISHU_APP_ID\", \"app_secret\": \"$FEISHU_APP_SECRET\"}" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tenant_access_token',''))")

# 使用文档内容API - 替换整个文档内容
curl -s -X PUT "https://open.feishu.cn/open-apis/docx/v1/documents/${DOC_ID}/content" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"document\": {\"title\": \"Test\", \"content\": [[{\"text\": \"$CONTENT\"}]]}}"
