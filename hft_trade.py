#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million - High Frequency Small Order Strategy
小单高频量化交易策略
"""
import ccxt
import time
from datetime import datetime

print("=" * 60)
print("Web3Million - High Frequency Small Order Trading")
print("=" * 60)

# Initialize exchange
e = ccxt.okx({
    'apiKey': 'b71ee824-5524-4cde-b818-b8e294c27d56',
    'secret': '76122A8879980469F474F042135584DB',
    'password': 'Qian159.',
    'testnet': True,
    'timeout': 60000
})

# Trading config
MAX_ORDER_SIZE_USD = 10  # Max $10 per order
TRADE_COUNT = 20  # Number of trades to execute
SYMBOL = 'BTC/USDT'

# Track stats
trades = []
profit_loss = 0
start_time = datetime.now()

def get_balance():
    b = e.fetch_balance()
    return b['free'].get('USDT', 0), b['free'].get('BTC', 0)

def get_price():
    t = e.fetch_ticker(SYMBOL)
    return t['last'], t['bid'], t['ask']

print(f"\nConfig:")
print(f"  Symbol: {SYMBOL}")
print(f"  Max Order: ${MAX_ORDER_SIZE_USD}")
print(f"  Trade Count: {TRADE_COUNT}")
print(f"  Start Time: {start_time.strftime('%H:%M:%S')}")

# Get initial balance
usdt, btc = get_balance()
price, bid, ask = get_price()
initial_total = usdt + btc * price

print(f"\nInitial Balance:")
print(f"  USDT: ${usdt:.2f}")
print(f"  BTC: {btc:.6f} (${btc * price:.2f})")
print(f"  Total: ${initial_total:.2f}")
print(f"  BTC Price: ${price}")

print(f"\n{'='*60}")
print("Starting High Frequency Trading...")
print(f"{'='*60}\n")

# High frequency loop
for i in range(TRADE_COUNT):
    try:
        # Get current price
        price, bid, ask = get_price()
        usdt, btc = get_balance()
        
        # Calculate order size ($5-10 range)
        order_usd = min(8, usdt * 0.5)  # Use $8 or 50% of USDT
        order_btc = order_usd / price
        
        # Alternate buy/sell based on position
        if i % 2 == 0 and usdt > 5:
            # BUY
            action = 'BUY'
            actual_btc = min(order_btc, usdt / price)
            if actual_btc * price >= 1:  # Min order check
                o = e.create_market_buy_order(SYMBOL, actual_btc)
                trades.append(('BUY', actual_btc, price, o['id']))
                print(f"[{i+1:2d}] BUY  {actual_btc:.6f} BTC @ ${price:.1f} | USDT: ${usdt:.2f}")
            else:
                print(f"[{i+1:2d}] SKIP (insufficient USDT)")
                continue
                
        elif btc * price > 5:
            # SELL
            action = 'SELL'
            actual_btc = min(order_btc / price * price, btc)  # Sell equivalent amount
            actual_btc = min(0.0001, btc)  # Small amount
            if actual_btc * price >= 1:
                o = e.create_market_sell_order(SYMBOL, actual_btc)
                trades.append(('SELL', actual_btc, price, o['id']))
                print(f"[{i+1:2d}] SELL {actual_btc:.6f} BTC @ ${price:.1f} | BTC: {btc:.6f}")
            else:
                print(f"[{i+1:2d}] SKIP (insufficient BTC)")
                continue
        else:
            print(f"[{i+1:2d}] WAIT (no position)")
            continue
        
        time.sleep(1)  # 1 second between trades
        
    except Exception as ex:
        print(f"[{i+1:2d}] ERROR: {str(ex)[:50]}")
        time.sleep(2)

# Final stats
print(f"\n{'='*60}")
print("FINAL RESULTS")
print(f"{'='*60}")

usdt_final, btc_final = get_balance()
price_final, _, _ = get_price()
final_total = usdt_final + btc_final * price_final

profit = final_total - initial_total
profit_pct = (profit / initial_total) * 100
elapsed = (datetime.now() - start_time).total_seconds()

print(f"Initial: ${initial_total:.2f}")
print(f"Final:   ${final_total:.2f}")
print(f"Profit:  ${profit:.2f} ({profit_pct:+.2f}%)")
print(f"Time:    {elapsed:.1f} seconds")
print(f"Trades:  {len(trades)} executed")

print(f"\nTrade Summary:")
buys = len([t for t in trades if t[0] == 'BUY'])
sells = len([t for t in trades if t[0] == 'SELL'])
print(f"  BUY:  {buys}")
print(f"  SELL: {sells}")

print(f"\nFinal Position:")
print(f"  USDT: ${usdt_final:.2f}")
print(f"  BTC:  {btc_final:.6f} (${btc_final * price_final:.2f})")
