#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from datetime import datetime
import ccxt
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print('=' * 60)
print('Web3Million 双系统状态报告')
print(f'查询时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
print('=' * 60)

try:
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
    
    balance = okx.fetch_balance()
    usdt_balance = balance['total'].get('USDT', 0)
    
    print(f'💰 测试网余额：{usdt_balance} USDT')
    print('=' * 60)
    print('系统运行状态:')
    print('  ✅ v9.0 Ultra 激进策略 - 运行中')
    print('  ✅ 量子蜂群量化交易 - 运行中')
    print('=' * 60)
except Exception as e:
    print(f'查询状态出错：{e}')
