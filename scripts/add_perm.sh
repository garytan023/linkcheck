#!/bin/bash
DOC_ID=$1

FEISHU_APP_ID=${FEISHU_APP_ID:-}
FEISHU_APP_SECRET=${FEISHU_APP_SECRET:-}

if [ -z "$FEISHU_APP_ID" ] || [ -z "$FEISHU_APP_SECRET" ]; then
  echo "错误: 缺少环境变量 FEISHU_APP_ID 或 FEISHU_APP_SECRET" >&2
  exit 1
fi

node -e "
const { Client } = require('@larksuiteoapi/node-sdk');
const feishu = new Client({appId: '$FEISHU_APP_ID', appSecret: '$FEISHU_APP_SECRET'});
feishu.drive.permissionMember.create({
  path: { token: '$DOC_ID' },
  params: { type: 'docx', need_notification: false },
  data: { member_type: 'openid', member_id: 'ou_d635f4f3d20ac474cf8575038b5d2b33', perm: 'full_access' }
}).then(r => console.log(JSON.stringify(r))).catch(e => console.error(e.message));
"
