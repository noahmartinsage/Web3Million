#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test OKX connection and execute trade"""
import ccxt
import json
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Initialize OKX testnet
exchange = ccxt.okx({
    'apiKey': 'b71ee824-5524-4cde-b818-b8e294c27d56',
    'secret': '76122A8879980469F474F042135584DB',
    'password': 'Qian159.',
    'testnet': True
})

print("=== Testing OKX Testnet ===\n")

try:
    # 1. Get account balance
    print("1. Fetching account balance...")
    balance = exchange.fetch_balance()
    print(f"   USDT available: {balance['free'].get('USDT', 0)}")
    print(f"   BTC available: {balance['free'].get('BTC', 0)}")
    print(f"   ETH available: {balance['free'].get('ETH', 0)}")
    
    # 2. Get BTC/USDT ticker
    print("\n2. Fetching BTC/USDT ticker...")
    ticker = exchange.fetch_ticker('BTC/USDT')
    print(f"   Last: ${ticker['last']}")
    print(f"   Bid: ${ticker['bid']}")
    print(f"   Ask: ${ticker['ask']}")
    
    # 3. Get positions
    print("\n3. Fetching positions...")
    try:
        positions = exchange.fetch_positions()
        print(f"   Current positions: {len(positions)}")
    except:
        print("   No positions or error")
    
    # 4. Test market buy order
    print("\n4. Testing market buy order...")
    usdt_balance = balance['free'].get('USDT', 0)
    print(f"   USDT balance: {usdt_balance}")
    
    if usdt_balance > 10:
        order = exchange.create_market_buy_order(
            symbol='BTC/USDT',
            amount=0.001
        )
        print(f"   Order ID: {order['id']}")
        print(f"   Status: {order['status']}")
        print(f"   Filled price: {order.get('average', 'N/A')}")
    else:
        print(f"   Insufficient USDT balance")
        
    print("\n=== OKX Testnet Connected Successfully! ===")
    
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()
