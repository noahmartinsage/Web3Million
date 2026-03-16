#!/usr/bin/env python3
import json, sys, io
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

try:
    import ccxt
    with open('okx_config.json', 'r') as f:
        c = json.load(f)
    
    okx = ccxt.okx({
        'apiKey': c['api_key'],
        'secret': c['secret_key'],
        'password': c['passphrase'],
        'options': {'defaultType': 'swap'}
    })
    okx.set_sandbox_mode(True)
    
    b = okx.fetch_balance()
    u = float(b['total'].get('USDT', 0))
    
    print(f"检查时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"当前余额：{u:.4f} USDT")
    print(f"初始余额：1288.57 USDT")
    print(f"PnL: {u-1288.57:+.4f} USDT ({(u-1288.57)/1288.57*100:+.2f}%)")
except Exception as e:
    print(f"连接失败：{e}")
    print("可能是网络问题或 OKX 测试网暂时不可用")
