#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million 多轨驱动超级启动器
启动：超频 V2 + 量子蜂巢 + 逐仓 10U + 神秘大仓同步
"""
import os
import sys
import subprocess
import threading
import time
from datetime import datetime

print("=" * 80)
print("Web3Million Multi-Track Drive System - Super Launcher")
print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

# 要启动的组件
COMPONENTS = [
    {"name": "量子蜂巢", "file": "quantum_agents.py", "desc": "量子高频交易智能体"},
    {"name": "量子蜂群狂暴版", "file": "quantum_swarm_frenzy.py", "desc": "20 智能体狂暴模式"},
    {"name": "逐仓 10U", "file": "isolated_10usdt.py", "desc": "逐仓以小博大策略"},
]

running_processes = []

def start_component(component):
    """启动单个组件"""
    name = component["name"]
    file = component["file"]
    desc = component["desc"]
    
    print(f"\n[{name}] Starting - {desc}")
    
    try:
        # 启动进程
        proc = subprocess.Popen(
            [sys.executable, file],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        running_processes.append((name, proc))
        print(f"[{name}] Started (PID: {proc.pid})")
    except Exception as e:
        print(f"[{name}] Start failed: {e}")

def monitor_processes():
    """监控所有进程"""
    print("\n" + "=" * 80)
    print("Monitoring system status...")
    print("=" * 80)
    
    while running_processes:
        for name, proc in running_processes[:]:
            if proc.poll() is not None:
                # 进程已终止
                stdout, stderr = proc.communicate()
                if stdout:
                    print(f"[{name}] 输出：{stdout[:500]}")
                if stderr:
                    print(f"[{name}] 错误：{stderr[:500]}")
                print(f"[{name}] Exited (code: {proc.returncode})")
                running_processes.remove((name, proc))
        
        time.sleep(5)

# 启动所有组件
print("\n开始启动组件...\n")

for component in COMPONENTS:
    start_component(component)
    time.sleep(2)  # 间隔启动

print("\n" + "=" * 80)
print(f"Started {len(running_processes)} components")
print("Monitoring... (Press Ctrl+C to stop)")
print("=" * 80 + "\n")

# 开始监控
try:
    monitor_processes()
except KeyboardInterrupt:
    print("\n\nStop signal received...")
    for name, proc in running_processes:
        proc.terminate()
        print(f"[{name}] Terminated")
    print("All components stopped")
