#!/usr/bin/env python3
import ccxt, json, time, sys, io
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

with open('okx_config.json') as f:
    config = json.load(f)

okx = ccxt.okx({
    'apiKey': config['api_key'],
    'secret': config['secret_key'],
    'password': config['passphrase'],
    'enableRateLimit': False,
    'options': {'defaultType': 'swap'}
})
okx.set_sandbox_mode(True)

# 获取 1 分钟 K 线
symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT']
print(f"{datetime.now().strftime('%H:%M:%S')} 实时数据:")
print("=" * 60)

for symbol in symbols:
    try:
        ohlcv = okx.fetch_ohlcv(symbol, '1m', limit=2)
        if len(ohlcv) >= 2:
            current = ohlcv[-1][4]
            prev = ohlcv[-2][4]
            change = (current - prev) / prev * 100
            print(f"{symbol}: ${current} (1 分钟：{change:+.2f}%)")
    except Exception as e:
        print(f"{symbol}: 获取失败")

# 检查持仓
print("\n持仓状态:")
try:
    positions = okx.fetch_positions()
    active = [p for p in positions if float(p.get('contracts', 0)) > 0]
    if active:
        for p in active:
            print(f"  {p['symbol']} {p.get('side')} {p.get('contracts')} @ {p.get('entryPrice')}")
    else:
        print("  无持仓 (空仓等待中)")
except Exception as e:
    print(f"  查询失败：{e}")
