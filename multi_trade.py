#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Web3Million Multi-Trade Strategy"""
import ccxt
import time

print("=" * 50)
print("Web3Million - Multi-Trade Strategy")
print("=" * 50)

e = ccxt.okx({
    'apiKey': 'b71ee824-5524-4cde-b818-b8e294c27d56',
    'secret': '76122A8879980469F474F042135584DB',
    'password': 'Qian159.',
    'testnet': True,
    'timeout': 60000
})

# Initial state
print("\n1. Getting initial balance...")
b = e.fetch_balance()
usdt = b['free'].get('USDT', 0)
btc = b['free'].get('BTC', 0)
eth = b['free'].get('ETH', 0)

t_btc = e.fetch_ticker('BTC/USDT')
t_eth = e.fetch_ticker('ETH/USDT')
initial_total = usdt + btc * t_btc['last'] + eth * t_eth['last']

print(f"   USDT: ${usdt:.2f}")
print(f"   BTC: {btc:.6f}")
print(f"   ETH: {eth:.6f}")
print(f"   Total: ${initial_total:.2f}")

trades = []

# Strategy: Buy low, sell high with small amounts
print("\n2. Executing trading strategy...")

# Trade 1: Buy 0.001 BTC
print("\n[Trade 1] BUY 0.001 BTC...")
o1 = e.create_market_buy_order('BTC/USDT', 0.001)
trades.append(('BUY', 0.001, 'BTC', o1['id']))
print(f"   Order: {o1['id']}")
time.sleep(2)

# Trade 2: Buy 0.001 BTC
print("\n[Trade 2] BUY 0.001 BTC...")
o2 = e.create_market_buy_order('BTC/USDT', 0.001)
trades.append(('BUY', 0.001, 'BTC', o2['id']))
print(f"   Order: {o2['id']}")
time.sleep(2)

# Trade 3: Sell 0.002 BTC (take profit)
print("\n[Trade 3] SELL 0.002 BTC...")
o3 = e.create_market_sell_order('BTC/USDT', 0.002)
trades.append(('SELL', 0.002, 'BTC', o3['id']))
print(f"   Order: {o3['id']}")
time.sleep(2)

# Trade 4: Buy 0.01 ETH
print("\n[Trade 4] BUY 0.01 ETH...")
o4 = e.create_market_buy_order('ETH/USDT', 0.01)
trades.append(('BUY', 0.01, 'ETH', o4['id']))
print(f"   Order: {o4['id']}")
time.sleep(2)

# Trade 5: Sell 0.01 ETH (quick flip)
print("\n[Trade 5] SELL 0.01 ETH...")
o5 = e.create_market_sell_order('ETH/USDT', 0.01)
trades.append(('SELL', 0.01, 'ETH', o5['id']))
print(f"   Order: {o5['id']}")
time.sleep(2)

# Final state
print("\n3. Getting final balance...")
b2 = e.fetch_balance()
usdt2 = b2['free'].get('USDT', 0)
btc2 = b2['free'].get('BTC', 0)
eth2 = b2['free'].get('ETH', 0)

t_btc2 = e.fetch_ticker('BTC/USDT')
t_eth2 = e.fetch_ticker('ETH/USDT')
final_total = usdt2 + btc2 * t_btc2['last'] + eth2 * t_eth2['last']

print(f"   USDT: ${usdt2:.2f}")
print(f"   BTC: {btc2:.6f}")
print(f"   ETH: {eth2:.6f}")
print(f"   Total: ${final_total:.2f}")

# Summary
print("\n" + "=" * 50)
print("TRADING SUMMARY")
print("=" * 50)
print(f"Initial: ${initial_total:.2f}")
print(f"Final:   ${final_total:.2f}")
print(f"Profit:  ${final_total - initial_total:.2f}")
print(f"Return:  {(final_total - initial_total) / initial_total * 100:.2f}%")
print(f"Trades:  {len(trades)}")

print("\nTrade History:")
for i, (action, amount, symbol, oid) in enumerate(trades, 1):
    print(f"  {i}. {action} {amount} {symbol} - {oid}")
