#!/usr/bin/env python3
import ccxt

okx = ccxt.okx({'enableRateLimit': True, 'options': {'defaultType': 'swap'}})
okx.set_sandbox_mode(True)
okx.timeout = 10000

print("Testing OKX testnet connection...")
try:
    ticker = okx.fetch_ticker('BTC/USDT:USDT')
    print(f"BTC Price: {ticker['last']}")
    print("Connection OK!")
except Exception as e:
    print(f"Error: {e}")
