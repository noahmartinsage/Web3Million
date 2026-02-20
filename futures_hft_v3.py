#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million - High Leverage Futures HFT v3
高倍合约高频交易 - 使用最小下单量 0.01 BTC
"""
import ccxt
import time
from datetime import datetime

print("=" * 60)
print("Web3Million - High Leverage Futures HFT v3")
print("=" * 60)

e = ccxt.okx({
    'apiKey': 'b71ee824-5524-4cde-b818-b8e294c27d56',
    'secret': '76122A8879980469F474F042135584DB',
    'password': 'Qian159.',
    'testnet': True,
    'timeout': 60000,
    'options': {'defaultType': 'swap'}
})

# Config - MIN order is 0.01 BTC (~$667)
LEVERAGE = 50
ORDER_SIZE = 0.01  # BTC - MINIMUM for OKX
TRADE_COUNT = 10
SYMBOL = 'BTC/USDT:USDT'

print(f"\nConfig:")
print(f"  Symbol: {SYMBOL}")
print(f"  Leverage: {LEVERAGE}x")
print(f"  Order Size: {ORDER_SIZE} BTC (~${ORDER_SIZE * 67000})")
print(f"  Effective Position: ${ORDER_SIZE * 67000 * LEVERAGE}")
print(f"  Trades: {TRADE_COUNT}")

# Set leverage
try:
    e.set_leverage(LEVERAGE, SYMBOL)
    print(f"  Leverage: {LEVERAGE}x ✓")
except Exception as ex:
    print(f"  Leverage: {str(ex)[:60]}")

trades = []
start_time = datetime.now()

def get_position():
    try:
        positions = e.fetch_positions([SYMBOL])
        for pos in positions:
            if pos['symbol'] == SYMBOL:
                return {
                    'size': float(pos['contracts']),
                    'side': pos['side'],
                    'pnl': float(pos['unrealizedPnl'] or 0)
                }
    except:
        pass
    return {'size': 0, 'side': None, 'pnl': 0}

def get_balance():
    b = e.fetch_balance()
    return b['free'].get('USDT', 0)

def get_price():
    t = e.fetch_ticker(SYMBOL)
    return t['last']

# Initial
usdt = get_balance()
pos = get_position()
price = get_price()
initial_total = usdt

print(f"\nInitial:")
print(f"  USDT: ${usdt:.2f}")
print(f"  Position: {pos['size']} {pos['side'] or 'NONE'}")
print(f"  Price: ${price}")

print(f"\n{'='*60}")
print("Trading...")
print(f"{'='*60}\n")

for i in range(TRADE_COUNT):
    try:
        price = get_price()
        pos = get_position()
        
        if i % 2 == 0:
            # LONG - close short first if any
            if pos['side'] == 'short' and pos['size'] > 0:
                e.create_market_order(SYMBOL, 'buy', pos['size'])
                trades.append(('CLOSE_SHORT', pos['size'], price))
                time.sleep(0.3)
            
            e.create_market_order(SYMBOL, 'buy', ORDER_SIZE)
            trades.append(('LONG', ORDER_SIZE, price))
            print(f"[{i+1:2d}] LONG  {ORDER_SIZE} BTC @ ${price:.0f}")
        else:
            # SHORT - close long first if any
            if pos['side'] == 'long' and pos['size'] > 0:
                e.create_market_order(SYMBOL, 'sell', pos['size'])
                trades.append(('CLOSE_LONG', pos['size'], price))
                time.sleep(0.3)
            
            e.create_market_order(SYMBOL, 'sell', ORDER_SIZE)
            trades.append(('SHORT', ORDER_SIZE, price))
            print(f"[{i+1:2d}] SHORT {ORDER_SIZE} BTC @ ${price:.0f}")
        
        time.sleep(0.5)
        
    except Exception as ex:
        print(f"[{i+1:2d}] ERROR: {str(ex)[:50]}")
        time.sleep(1)

# Close
print(f"\n{'='*60}")
print("Closing...")
pos = get_position()
if pos['size'] > 0:
    side = 'sell' if pos['side'] == 'long' else 'buy'
    e.create_market_order(SYMBOL, side, pos['size'])
    print(f"  Closed {pos['size']} {pos['side']}")

# Results
usdt_final = get_balance()
pnl = usdt_final - initial_total
elapsed = (datetime.now() - start_time).total_seconds()

print(f"\n{'='*60}")
print("RESULTS")
print(f"{'='*60}")
print(f"Initial: ${initial_total:.2f}")
print(f"Final:   ${usdt_final:.2f}")
print(f"Profit:  ${pnl:.2f} ({pnl/initial_total*100:+.2f}%)")
print(f"Time:    {elapsed:.1f}s")
print(f"Trades:  {len(trades)}")
