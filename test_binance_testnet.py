#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test Binance Testnet Connection"""
import ccxt
import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("Binance Testnet Connection Test")
print("=" * 60)

api_key = os.getenv('BINANCE_TESTNET_API_KEY')
secret = os.getenv('BINANCE_TESTNET_SECRET_KEY')

print(f"API Key: {api_key[:20]}...")
print(f"Secret: {secret[:20]}...")

exchange = ccxt.binanceusdm({
    'apiKey': api_key,
    'secret': secret,
    'enableRateLimit': True,
    'options': {'defaultType': 'future'}
})

exchange.set_sandbox_mode(True)

try:
    print("\n[1/3] Loading markets...")
    exchange.load_markets()
    print("[OK] Markets loaded!")
    
    print("\n[2/3] Fetching balance...")
    balance = exchange.fetch_balance()
    print(f"[OK] Balance fetched!")
    print(f"    USDT: {balance.get('USDT', {}).get('free', 'N/A')}")
    
    print("\n[3/3] Fetching BTC ticker...")
    ticker = exchange.fetch_ticker('BTC/USDT:USDT')
    print(f"[OK] BTC Price: ${ticker.get('last', 'N/A'):,.2f}")
    
    print("\n" + "=" * 60)
    print("SUCCESS - Binance Testnet connection working!")
    print("=" * 60)
    
except ccxt.NetworkError as e:
    print(f"\n[ERROR] Network Error: {e}")
except ccxt.AuthenticationError as e:
    print(f"\n[ERROR] Auth Error: {e}")
except Exception as e:
    print(f"\n[ERROR] {type(e).__name__}: {e}")
