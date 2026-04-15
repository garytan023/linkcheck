#!/usr/bin/env python3
import sys
sys.path.insert(0, '/Users/garytan/.openclaw/workspace-dev/skills/knowledge-compiler/scripts')
from kk_compile import main
sys.argv = ['kk_compile.py', '/Users/garytan/Documents/garytan/宇先生/知识库/karpathy-pkm', '--build-wiki']
main()
