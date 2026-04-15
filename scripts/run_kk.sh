#!/bin/bash
KK="/Users/garytan/Documents/garytan/宇先生/知识库/karpathy-pkm"
SKILL="/Users/garytan/.openclaw/workspace-dev/skills/knowledge-compiler/scripts"
cd "$SKILL"
python3 kk_compile.py "$KK" --build-wiki 2>&1
echo "---UPDATE-DEX---"
python3 kk_compile.py "$KK" --update-index 2>&1
