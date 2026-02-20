#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million - High Leverage Futures HFT v2
高倍合约高频交易 - 修正最小下单量
"""
import ccxt
import time
from datetime import datetime

print("=" * 60)
print("Web3Million - High Leverage Futures HFT v2")
print("=" * 60)

e = ccxt.okx({
    'apiKey': 'b71ee824-5524-4cde-b818-b8e294c27d56',
    'secret': '76122A8879980469F474F042135584DB',
    'password': 'Qian159.',
    'testnet': True,
    'timeout': 60000,
    'options': {'defaultType': 'swap'}
})

# Config - adjusted for minimum order size
LEVERAGE = 50
ORDER_SIZE_USD = 50  # Increased to $50 per order (min ~0.001 BTC)
TRADE_COUNT = 20
SYMBOL = 'BTC/USDT:USDT'

print(f"\nConfig:")
print(f"  Symbol: {SYMBOL}")
print(f"  Leverage: {LEVERAGE}x")
print(f"  Order Size: ${ORDER_SIZE_USD}")
print(f"  Effective Position: ${ORDER_SIZE_USD * LEVERAGE}")
print(f"  Trades: {TRADE_COUNT}")

# Set leverage
try:
    e.set_leverage(LEVERAGE, SYMBOL)
    print(f"  Leverage set to {LEVERAGE}x!")
except Exception as ex:
    print(f"  Leverage: {str(ex)[:80]}")

trades = []
start_time = datetime.now()

def get_position():
    try:
        positions = e.fetch_positions([SYMBOL])
        for pos in positions:
            if pos['symbol'] == SYMBOL:
                return {
                    'size': float(pos['contracts']) if pos['contracts'] else 0,
                    'side': pos['side'],
                    'pnl': float(pos['unrealizedPnl']) if pos['unrealizedPnl'] else 0
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

# Initial state
usdt = get_balance()
pos = get_position()
price = get_price()

print(f"\nInitial:")
print(f"  USDT: ${usdt:.2f}")
print(f"  Position: {pos['size']} {pos['side'] or 'NONE'}")
print(f"  Price: ${price}")

print(f"\n{'='*60}")
print("Starting Trading...")
print(f"{'='*60}\n")

for i in range(TRADE_COUNT):
    try:
        price = get_price()
        pos = get_position()
        
        # Min order: 0.001 BTC (~$67 at current price)
        order_size = 0.001
        
        if i % 2 == 0:
            # LONG
            if pos['side'] == 'short' and pos['size'] > 0:
                e.create_market_order(SYMBOL, 'buy', pos['size'])
                trades.append(('CLOSE_SHORT', pos['size'], price))
                time.sleep(0.3)
            
            e.create_market_order(SYMBOL, 'buy', order_size)
            trades.append(('LONG', order_size, price))
            pnl = pos.get('pnl', 0)
            print(f"[{i+1:2d}] LONG  {order_size} BTC @ ${price:.1f} | PnL: ${pnl:.2f}")
        else:
            # SHORT
            if pos['side'] == 'long' and pos['size'] > 0:
                e.create_market_order(SYMBOL, 'sell', pos['size'])
                trades.append(('CLOSE_LONG', pos['size'], price))
                time.sleep(0.3)
            
            e.create_market_order(SYMBOL, 'sell', order_size)
            trades.append(('SHORT', order_size, price))
            pnl = pos.get('pnl', 0)
            print(f"[{i+1:2d}] SHORT {order_size} BTC @ ${price:.1f} | PnL: ${pnl:.2f}")
        
        time.sleep(0.5)
        
    except Exception as ex:
        print(f"[{i+1:2d}] ERROR: {str(ex)[:50]}")
        time.sleep(1)

# Close position
print(f"\n{'='*60}")
print("Closing position...")
pos = get_position()
if pos['size'] > 0:
    if pos['side'] == 'long':
        e.create_market_order(SYMBOL, 'sell', pos['size'])
    else:
        e.create_market_order(SYMBOL, 'buy', pos['size'])
    print(f"  Closed {pos['size']} {pos['side']}")

# Results
usdt_final = get_balance()
pnl = usdt_final - usdt
elapsed = (datetime.now() - start_time).total_seconds()

print(f"\n{'='*60}")
print("RESULTS")
print(f"{'='*60}")
print(f"Initial: ${usdt:.2f}")
print(f"Final:   ${usdt_final:.2f}")
print(f"Profit:  ${pnl:.2f} ({pnl/usdt*100:+.2f}%)")
print(f"Time:    {elapsed:.1f}s")
print(f"Trades:  {len(trades)}")
