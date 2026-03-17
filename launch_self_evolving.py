#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million 自我进化启动器
- 启动量子蜂巢多轨驱动系统
- 自动监控和重启
- 定期 Git 提交和推送
- 百万目标进度追踪
"""
import os
import sys
import subprocess
import time
import json
from datetime import datetime
from pathlib import Path

print("=" * 80)
print("Web3Million Self-Evolving Launcher")
print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("Target: $1,000,000 | Components: Quantum Hive + Swarm + Isolated 10U")
print("=" * 80)

WORKSPACE = Path(__file__).parent
GIT_INTERVAL_MINUTES = 30
last_git_push = datetime.now()

def check_and_push_git():
    """检查并推送 Git"""
    global last_git_push
    now = datetime.now()
    elapsed = (now - last_git_push).total_seconds() / 60
    
    if elapsed >= GIT_INTERVAL_MINUTES:
        print(f"\n[{now.strftime('%H:%M')}] Git auto-push...")
        try:
            # Add
            subprocess.run(['git', 'add', '-A'], cwd=WORKSPACE, timeout=30)
            # Commit
            msg = f"Auto-commit: Progress update at {now.strftime('%Y-%m-%d %H:%M')}"
            subprocess.run(['git', 'commit', '-m', msg], cwd=WORKSPACE, timeout=30)
            # Push
            subprocess.run(['git', 'push', 'origin', 'main'], cwd=WORKSPACE, timeout=60)
            print("[OK] Git push completed")
            last_git_push = now
        except Exception as e:
            print(f"[WARN] Git push failed: {e}")

def run_quantum_agents():
    """运行量子蜂巢"""
    print("\n" + "=" * 80)
    print("Starting Quantum Hive (quantum_agents.py)")
    print("=" * 80)
    proc = subprocess.Popen(
        [sys.executable, 'quantum_agents.py'],
        cwd=WORKSPACE
    )
    return proc

def run_swarm_frenzy():
    """运行量子蜂群狂暴版"""
    print("\n" + "=" * 80)
    print("Starting Quantum Swarm Frenzy (quantum_swarm_frenzy.py)")
    print("=" * 80)
    proc = subprocess.Popen(
        [sys.executable, 'quantum_swarm_frenzy.py'],
        cwd=WORKSPACE
    )
    return proc

def run_isolated_10u():
    """运行逐仓 10U"""
    print("\n" + "=" * 80)
    print("Starting Isolated 10USDT (isolated_10usdt.py)")
    print("=" * 80)
    proc = subprocess.Popen(
        [sys.executable, 'isolated_10usdt.py'],
        cwd=WORKSPACE
    )
    return proc

def monitor_and_restart():
    """监控并重启组件"""
    print("\n" + "=" * 80)
    print("Monitoring components...")
    print("Press Ctrl+C to stop all")
    print("=" * 80 + "\n")
    
    processes = {
        'quantum_agents': None,
        'swarm_frenzy': None,
        'isolated_10u': None
    }
    
    # 启动所有组件
    processes['quantum_agents'] = run_quantum_agents()
    time.sleep(3)
    processes['swarm_frenzy'] = run_swarm_frenzy()
    time.sleep(3)
    processes['isolated_10u'] = run_isolated_10u()
    
    # 监控循环
    git_start = datetime.now()
    while True:
        time.sleep(10)
        
        # 检查 Git 推送
        if (datetime.now() - git_start).total_seconds() >= GIT_INTERVAL_MINUTES * 60:
            check_and_push_git()
            git_start = datetime.now()
        
        # 检查进程
        for name, proc in processes.items():
            if proc and proc.poll() is not None:
                print(f"[{name}] Process exited (code: {proc.returncode}), restarting...")
                if name == 'quantum_agents':
                    processes[name] = run_quantum_agents()
                elif name == 'swarm_frenzy':
                    processes[name] = run_swarm_frenzy()
                elif name == 'isolated_10u':
                    processes[name] = run_isolated_10u()

if __name__ == '__main__':
    try:
        monitor_and_restart()
    except KeyboardInterrupt:
        print("\n\nStopping all components...")
        # 终止所有子进程
        for proc in [p for p in [run_quantum_agents(), run_swarm_frenzy(), run_isolated_10u()] if p]:
            proc.terminate()
        print("All stopped.")
