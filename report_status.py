#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Web3Million 量子蜂巢完整状态报告"""
import os, sys, io, json

# Windows 强制 UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import ccxt
from datetime import datetime

print("=" * 70)
print("🦊 Web3Million 量子蜂巢状态报告")
print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

# 1. OKX 账户余额
print("\n【1】OKX 测试网账户")
try:
    with open('okx_config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    okx = ccxt.okx({
        'apiKey': config['api_key'],
        'secret': config['secret_key'],
        'password': config['passphrase'],
        'enableRateLimit': True,
        'options': {'defaultType': 'swap'}
    })
    okx.set_sandbox_mode(True)
    okx.session.trust_env = False
    okx.session.proxies = {}
    
    balance = okx.fetch_balance()
    usdt = balance.get('USDT', {})
    btc = balance.get('BTC', 0)
    eth = balance.get('ETH', 0)
    okb = balance.get('OKB', 0)
    
    print(f"  USDT 总额：{usdt.get('total', 0):.2f}")
    print(f"  USDT 可用：{usdt.get('free', 0):.2f}")
    print(f"  USDT 冻结：{usdt.get('used', 0):.2f}")
    if isinstance(btc, (int, float)):
        print(f"  BTC: {btc:.6f}")
    if isinstance(eth, (int, float)):
        print(f"  ETH: {eth:.4f}")
    if isinstance(okb, (int, float)):
        print(f"  OKB: {okb:.2f}")
except Exception as e:
    print(f"  错误：{e}")

# 2. 量子蜂群统计
print("\n【2】量子蜂群统计")
try:
    with open('quantum_hive.log', 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        lines = content.split('\n')
        
        # 查找统计行
        stats_line = None
        for line in reversed(lines):
            if '运行' in line and 'PnL' in line:
                stats_line = line
                break
        
        if stats_line:
            print(f"  原始统计：{stats_line[:200]}")
        
        # 计算交易统计
        win_count = content.count('WIN')
        loss_count = content.count('LOSS')
        total_trades = win_count + loss_count
        
        print(f"  日志总行数：{len(lines)}")
        print(f"  WIN 次数：{win_count}")
        print(f"  LOSS 次数：{loss_count}")
        if total_trades > 0:
            win_rate = win_count / total_trades * 100
            print(f"  胜率：{win_rate:.1f}%")
except Exception as e:
    print(f"  错误：{e}")

# 3. 智能体状态
print("\n【3】智能体活动")
try:
    with open('quantum_hive.log', 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        print("  最新 10 条活动:")
        for i, line in enumerate(lines[-10:]):
            if line.strip():
                print(f"    {line.strip()[:100]}")
except Exception as e:
    print(f"  错误：{e}")

# 4. 系统状态
print("\n【4】系统文件状态")
files_to_check = [
    'perp_trader_v7_2.py',
    'quantum_simple_v2.py',
    'quantum_hive.log',
    'sim_trader.log'
]
for fname in files_to_check:
    if os.path.exists(fname):
        size = os.path.getsize(fname)
        mtime = datetime.fromtimestamp(os.path.getmtime(fname))
        print(f"  {fname}: {size:,} bytes (更新：{mtime.strftime('%m-%d %H:%M')})")
    else:
        print(f"  {fname}: 不存在")

print("\n" + "=" * 70)
print("报告完成")
print("=" * 70)
