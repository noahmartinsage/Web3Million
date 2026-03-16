#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
双系统并发测试 - v9.0 Ultra + 量子蜂群
"""
import subprocess
import time
import sys
from datetime import datetime

print("=" * 80)
print("🚀 Web3Million 双系统测试启动")
print(f"启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

# 启动 v9.0 Ultra
print("\n1️⃣ 启动 v9.0 Ultra 激进策略...")
v9_proc = subprocess.Popen(
    [sys.executable, 'perp_trader_v9_ultra.py'],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    encoding='utf-8',
    errors='replace'
)

# 启动量子蜂群
print("2️⃣ 启动量子蜂群量化交易...")
swarm_proc = subprocess.Popen(
    [sys.executable, 'quantum_swarm_trader.py'],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    encoding='utf-8',
    errors='replace'
)

print("\n✅ 双系统已启动，开始监控输出...\n")

try:
    while True:
        # 读取 v9 输出
        if v9_proc.poll() is None:
            line = v9_proc.stdout.readline()
            if line:
                print(f"[V9] {line.strip()}")
        
        # 读取蜂群输出
        if swarm_proc.poll() is None:
            line = swarm_proc.stdout.readline()
            if line:
                print(f"[SWARM] {line.strip()}")
        
        if v9_proc.poll() is not None and swarm_proc.poll() is not None:
            break
            
        time.sleep(0.5)
        
except KeyboardInterrupt:
    print("\n🛑 停止测试")
    v9_proc.terminate()
    swarm_proc.terminate()
