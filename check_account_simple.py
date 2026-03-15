#!/usr/bin/env python3
import ccxt
import json
from datetime import datetime
import sys

# 设置 UTF-8 编码
sys.stdout.reconfigure(encoding='utf-8')

# 加载配置
with open('okx_config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

print("=" * 50)
print("OKX Testnet Account Status")
print("=" * 50)
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 初始化 OKX 测试网
okx = ccxt.okx({
    'apiKey': config['api_key'],
    'secret': config['secret_key'],
    'password': config['passphrase'],
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})
okx.set_sandbox_mode(True)

# 尝试连接
try:
    print("Connecting to OKX testnet...")
    balance = okx.fetch_balance()
    print()
    print("Balance:")
    print(f"  USDT Available: {balance['free'].get('USDT', 0):.2f}")
    print(f"  USDT Total: {balance['total'].get('USDT', 0):.2f}")
    print()
    
    positions = okx.fetch_positions()
    active = [p for p in positions if p.get('contracts') and float(p['contracts']) > 0]
    print("Positions:")
    if active:
        for p in active:
            side = "LONG" if p['side'] == 'long' else "SHORT"
            print(f"  {p['symbol']}: {side} {p['contracts']} @ {p['entryPrice'] or '0'}")
    else:
        print("  No active positions")
    print()
    
except Exception as e:
    print(f"Connection Error: {e}")
    print()
    print("Trying with proxy...")
    
    # 尝试使用代理
    try:
        okx_with_proxy = ccxt.okx({
            'apiKey': config['api_key'],
            'secret': config['secret_key'],
            'password': config['passphrase'],
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'},
            'proxies': {
                'http': 'http://127.0.0.1:7890',
                'https': 'https://127.0.0.1:7890',
            }
        })
        okx_with_proxy.set_sandbox_mode(True)
        balance = okx_with_proxy.fetch_balance()
        print()
        print("Balance (via proxy):")
        print(f"  USDT Available: {balance['free'].get('USDT', 0):.2f}")
        print(f"  USDT Total: {balance['total'].get('USDT', 0):.2f}")
    except Exception as e2:
        print(f"Proxy also failed: {e2}")
        print()
        print("Suggestion: Check if proxy is running or use IP direct connection")

print()
print("=" * 50)
