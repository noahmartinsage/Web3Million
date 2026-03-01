#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test Binance Public API (No Auth Required)"""
import ccxt

print("=" * 60)
print("Binance Public API Test")
print("=" * 60)

exchange = ccxt.binance({
    'enableRateLimit': True,
})

try:
    print("\n[1/3] Loading markets...")
    exchange.load_markets()
    print(f"[OK] Markets loaded! ({len(exchange.markets)} pairs)")
    
    print("\n[2/3] Fetching BTC/USDT ticker...")
    ticker = exchange.fetch_ticker('BTC/USDT')
    print(f"[OK] BTC Price: ${ticker.get('last', 0):,.2f}")
    print(f"    24h Change: {ticker.get('percentage', 0):.2f}%")
    
    print("\n[3/3] Fetching ETH/USDT ticker...")
    ticker = exchange.fetch_ticker('ETH/USDT')
    print(f"[OK] ETH Price: ${ticker.get('last', 0):,.2f}")
    print(f"    24h Change: {ticker.get('percentage', 0):.2f}%")
    
    print("\n" + "=" * 60)
    print("SUCCESS - Binance Public API working!")
    print("=" * 60)
    print("\nNote: Testnet API keys may need special handling.")
    print("Consider using paper trading mode for testing.")
    
except ccxt.NetworkError as e:
    print(f"\n[ERROR] Network Error: {e}")
except Exception as e:
    print(f"\n[ERROR] {type(e).__name__}: {e}")
