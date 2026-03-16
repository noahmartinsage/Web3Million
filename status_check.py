#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, ccxt, sys, io
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

with open('okx_config.json', 'r') as f:
    config = json.load(f)

okx = ccxt.okx({
    'apiKey': config['api_key'],
    'secret': config['secret_key'],
    'password': config['passphrase'],
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})
okx.set_sandbox_mode(True)

# 获取余额
balance = okx.fetch_balance()
usdt = float(balance['total'].get('USDT', 0))

# 获取未平仓合约
positions = okx.fetch_positions()
active_positions = [p for p in positions if float(p.get('contracts', 0)) > 0]

print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"余额：{usdt:.4f} USDT")
print(f"未平仓合约：{len(active_positions)}")
if active_positions:
    for p in active_positions[:5]:
        print(f"  - {p['symbol']}: {p['side']} {p['contracts']} @ {p['entryPrice']}")
else:
    print("  无未平仓合约")

# 初始余额参考
print(f"\n初始余额：1288.57 USDT")
pnl = usdt - 1288.57
print(f"PnL: {pnl:+.4f} USDT ({pnl/1288.57*100:+.2f}%)")
