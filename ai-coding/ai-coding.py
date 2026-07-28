#!/usr/bin/env python3
"""AI Coding 主入口"""
import sys
import os
from pathlib import Path

# 添加 src 到路径
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir / "src"))

from cli import main

if __name__ == "__main__":
    sys.exit(main())