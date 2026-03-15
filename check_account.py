#!/usr/bin/env python3
import ccxt
import json
from datetime import datetime

# 加载配置
with open('okx_config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# 初始化 OKX 测试网 - 使用 IP 直连绕过 DNS 劫持
okx = ccxt.okx({
    'apiKey': config['api_key'],
    'secret': config['secret_key'],
    'password': config['passphrase'],
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})
okx.set_sandbox_mode(True)
# 使用 IP 直连 (43.199.3.187) 绕过 DNS 劫持
okx.urls['public'] = 'https://43.199.3.187'
okx.urls['private'] = 'https://43.199.3.187'
okx.urls['test'] = 'https://43.199.3.187'

print("=" * 50)
print("OKX Testnet Account Status")
print("=" * 50)
print(f"查询时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 获取余额
try:
    balance = okx.fetch_balance()
    print("Balance:")
    print(f"  USDT 可用：{balance['free'].get('USDT', 0):.2f}")
    print(f"  USDT 总额：{balance['total'].get('USDT', 0):.2f}")
    print()
except Exception as e:
    print(f"Error fetching balance: {e}")
    print()

# 获取持仓
try:
    print("Positions:")
    positions = okx.fetch_positions()
    active_positions = [p for p in positions if p.get('contracts') and float(p['contracts']) > 0]
    
    if active_positions:
        for p in active_positions:
            side = "多" if p['side'] == 'long' else "空"
            print(f"  {p['symbol']}: {side} {p['contracts']} @ {p['entryPrice'] or '0'}")
    else:
        print("  无持仓")
    print()
except Exception as e:
    print(f"Error fetching positions: {e}")
    print()

# 获取最近订单
try:
    print("Recent Orders (max 5):")
    orders = okx.fetch_orders(limit=5)
    if orders:
        for o in orders[:5]:
            status = "✅" if o['status'] == 'closed' else "⏳"
            print(f"  {status} {o['symbol']} {o['side']} {o['amount']} @ {o['price'] or o['average'] or '-'}")
    else:
        print("  无订单记录")
except Exception as e:
    print(f"Error fetching orders: {e}")

print()
print("=" * 50)
