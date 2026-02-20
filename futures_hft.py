#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million - High Leverage Futures HFT Strategy
高倍合约高频量化交易策略
"""
import ccxt
import time
from datetime import datetime

print("=" * 60)
print("Web3Million - High Leverage Futures HFT")
print("=" * 60)

# Initialize OKX with swap/futures
e = ccxt.okx({
    'apiKey': 'b71ee824-5524-4cde-b818-b8e294c27d56',
    'secret': '76122A8879980469F474F042135584DB',
    'password': 'Qian159.',
    'testnet': True,
    'timeout': 60000,
    'options': {
        'defaultType': 'swap',  # Use perpetual swaps
    }
})

# Trading config
LEVERAGE = 50  # 50x leverage
ORDER_SIZE_USD = 10  # $10 per order
TRADE_COUNT = 30  # Number of trades
SYMBOL = 'BTC/USDT:USDT'  # Swap symbol

print(f"\nConfig:")
print(f"  Symbol: {SYMBOL}")
print(f"  Leverage: {LEVERAGE}x")
print(f"  Order Size: ${ORDER_SIZE_USD}")
print(f"  Effective Position: ${ORDER_SIZE_USD * LEVERAGE}")
print(f"  Trade Count: {TRADE_COUNT}")

# Set leverage
try:
    print(f"\nSetting leverage to {LEVERAGE}x...")
    e.set_leverage(LEVERAGE, SYMBOL)
    print("  Leverage set successfully!")
except Exception as ex:
    print(f"  Leverage warning: {str(ex)[:100]}")

trades = []
start_time = datetime.now()

def get_position():
    """Get current position"""
    try:
        positions = e.fetch_positions([SYMBOL])
        for pos in positions:
            if pos['symbol'] == SYMBOL:
                return {
                    'size': float(pos['contracts']) if pos['contracts'] else 0,
                    'side': pos['side'],
                    'unrealized_pnl': float(pos['unrealizedPnl']) if pos['unrealizedPnl'] else 0
                }
    except:
        pass
    return {'size': 0, 'side': None, 'unrealized_pnl': 0}

def get_balance():
    """Get USDT balance"""
    b = e.fetch_balance()
    return b['free'].get('USDT', 0)

def get_price():
    """Get current price"""
    t = e.fetch_ticker(SYMBOL)
    return t['last'], t['bid'], t['ask']

# Initial state
print(f"\nInitial State:")
usdt = get_balance()
pos = get_position()
price, bid, ask = get_price()
print(f"  USDT Balance: ${usdt:.2f}")
print(f"  Position: {pos['size']} {pos['side'] or 'NONE'}")
print(f"  BTC Price: ${price}")

print(f"\n{'='*60}")
print("Starting High Leverage HFT...")
print(f"{'='*60}\n")

# HFT Loop
for i in range(TRADE_COUNT):
    try:
        price, bid, ask = get_price()
        pos = get_position()
        usdt = get_balance()
        
        # Calculate order size in contracts
        contract_size = ORDER_SIZE_USD / price
        
        # Simple momentum strategy
        if i % 2 == 0:
            # Open/Increase LONG
            if pos['side'] != 'long':
                # Close any short first
                if pos['side'] == 'short' and pos['size'] > 0:
                    e.create_market_order(SYMBOL, 'buy', pos['size'])
                    trades.append(('CLOSE_SHORT', pos['size'], price))
                    time.sleep(0.5)
                
                # Open long
                e.create_market_order(SYMBOL, 'buy', contract_size)
                trades.append(('OPEN_LONG', contract_size, price))
                print(f"[{i+1:2d}] OPEN LONG  {contract_size:.5f} BTC @ ${price:.1f}")
            else:
                print(f"[{i+1:2d}] HOLD LONG  {pos['size']:.5f} BTC | PnL: ${pos['unrealized_pnl']:.2f}")
                
        else:
            # Open/Increase SHORT
            if pos['side'] != 'short':
                # Close any long first
                if pos['side'] == 'long' and pos['size'] > 0:
                    e.create_market_order(SYMBOL, 'sell', pos['size'])
                    trades.append(('CLOSE_LONG', pos['size'], price))
                    time.sleep(0.5)
                
                # Open short
                e.create_market_order(SYMBOL, 'sell', contract_size)
                trades.append(('OPEN_SHORT', contract_size, price))
                print(f"[{i+1:2d}] OPEN SHORT {contract_size:.5f} BTC @ ${price:.1f}")
            else:
                print(f"[{i+1:2d}] HOLD SHORT {pos['size']:.5f} BTC | PnL: ${pos['unrealized_pnl']:.2f}")
        
        time.sleep(1)  # 1 second between trades
        
    except Exception as ex:
        print(f"[{i+1:2d}] ERROR: {str(ex)[:60]}")
        time.sleep(2)

# Close all positions
print(f"\n{'='*60}")
print("Closing all positions...")
pos = get_position()
if pos['size'] > 0:
    if pos['side'] == 'long':
        e.create_market_order(SYMBOL, 'sell', pos['size'])
        print(f"  Closed LONG {pos['size']:.5f}")
    else:
        e.create_market_order(SYMBOL, 'buy', pos['size'])
        print(f"  Closed SHORT {pos['size']:.5f}")

# Final stats
print(f"\n{'='*60}")
print("FINAL RESULTS")
print(f"{'='*60}")

usdt_final = get_balance()
elapsed = (datetime.now() - start_time).total_seconds()

# Calculate PnL
pnl = usdt_final - usdt
pnl_pct = (pnl / usdt) * 100 if usdt > 0 else 0

print(f"Initial USDT: ${usdt:.2f}")
print(f"Final USDT:   ${usdt_final:.2f}")
print(f"Profit:       ${pnl:.2f} ({pnl_pct:+.2f}%)")
print(f"Time:         {elapsed:.1f} seconds")
print(f"Trades:       {len(trades)} executed")

print(f"\nTrade History:")
for i, (action, size, price) in enumerate(trades[:10], 1):
    print(f"  {i}. {action}: {size:.5f} @ ${price:.1f}")
if len(trades) > 10:
    print(f"  ... and {len(trades)-10} more trades")
