#!/usr/bin/env python3
import sys, json
from pathlib import Path
sys.path.insert(0, "/Users/garytan/.openclaw/workspace-dev/skills/knowledge-compiler/scripts")
from kk_compile import update_master_index

ws = Path("/Users/garytan/Documents/garytan/宇先生/知识库/karpathy-pkm")
update_master_index(ws)
