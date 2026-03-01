#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test Binance Testnet - Direct API Keys"""
import ccxt

print("=" * 60)
print("Binance Testnet Connection Test (Direct)")
print("=" * 60)

# 直接使用老板提供的 API 密钥
api_key = '1a3250b36d5a27ccc0e6a0125d98d1556ff9eacc78baa1fd9ecb1be09056c8f4'
secret = '6de29564a693aad4a969049d5accb6175fcd88be7dc4f2283e598d9a271c8505'

print(f"API Key: {api_key[:20]}...")
print(f"Secret: {secret[:20]}...")

# 使用币安现货测试网
exchange = ccxt.binance({
    'apiKey': api_key,
    'secret': secret,
    'enableRateLimit': True,
    'urls': {
        'api': {
            'public': 'https://testnet.binance.vision/api',
            'private': 'https://testnet.binance.vision/api',
        }
    },
    'options': {'defaultType': 'spot'}
})

try:
    print("\n[1/3] Loading markets...")
    exchange.load_markets()
    print("[OK] Markets loaded!")
    
    print("\n[2/3] Fetching balance...")
    balance = exchange.fetch_balance()
    print(f"[OK] Balance fetched!")
    usdt = balance.get('USDT', {})
    print(f"    USDT: {usdt.get('free', 'N/A')}")
    
    print("\n[3/3] Fetching BTC/USDT ticker...")
    ticker = exchange.fetch_ticker('BTC/USDT')
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
