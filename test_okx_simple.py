#!/usr/bin/env python3
"""Simple OKX API test without load_markets"""
import ccxt
import sys

print("Testing OKX Testnet - Simple Connection...")

exchange = ccxt.okx({
    'apiKey': 'b71ee824-5524-4cde-b818-b8e294c27d56',
    'secret': '76122A8879980469F474F042135584DB',
    'password': 'Qian159.',
    'timeout': 30000,
})

exchange.sandbox = True

try:
    # Try simple public API first
    print("Testing public API (fetch ticker)...")
    ticker = exchange.fetch_ticker('BTC/USDT:USDT')
    print(f"✓ BTC Price: ${ticker.get('last', 'N/A')}")
    
    # Try private API
    print("Testing private API (fetch balance)...")
    balance = exchange.fetch_balance()
    print(f"✓ USDT Balance: {balance.get('USDT', {}).get('free', 'N/A')}")
    
    print("\n✓ Connection successful!")
except ccxt.NetworkError as e:
    print(f"✗ Network Error: {e}")
except ccxt.AuthenticationError as e:
    print(f"✗ Auth Error: {e}")
except Exception as e:
    print(f"✗ Error: {type(e).__name__}: {e}")
