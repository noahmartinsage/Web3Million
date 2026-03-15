#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""快速启动量子蜂巢 - 带日志输出"""
import sys
import io

# 强制 UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import os
os.chdir('C:\\Users\\noah\\.openclaw\\workspace')

# 导入并运行
import quantum_agents

print("=" * 60)
print("启动量子蜂巢...")
print("=" * 60)

hive = quantum_agents.QuantumHive(
    initial_capital_per_agent=10.0,
    max_agents=10,
    leverage_range=(25, 50)
)

print("蜂巢已创建，开始运行...")
hive.run()
