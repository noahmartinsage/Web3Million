#!/usr/bin/env python3
import ccxt, json, sys, io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

with open('okx_config.json') as f:
    c = json.load(f)

okx = ccxt.okx({
    'apiKey': c['api_key'],
    'secret': c['secret_key'],
    'password': c['passphrase'],
    'options': {'defaultType': 'swap'}
})
okx.set_sandbox_mode(True)

try:
    b = okx.fetch_balance()
    u = float(b['total'].get('USDT', 0))
    print(f'OKX 连接成功！')
    print(f'余额：{u:.2f} USDT')
    print(f'初始：1288.57 USDT')
    print(f'PnL: {u-1288.57:+.2f} USDT')
except Exception as e:
    print(f'连接失败：{e}')
