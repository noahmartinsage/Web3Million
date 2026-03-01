#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test Binance Vision Testnet"""
import ccxt

print("=" * 60)
print("Binance Vision Testnet Test")
print("=" * 60)

api_key = '1a3250b36d5a27ccc0e6a0125d98d1556ff9eacc78baa1fd9ecb1be09056c8f4'
secret = '6de29564a693aad4a969049d5accb6175fcd88be7dc4f2283e598d9a271c8505'

print(f"API Key: {api_key[:20]}...")
print(f"Secret: {secret[:20]}...")

# Binance Vision Testnet (现货)
exchange = ccxt.binance({
    'apiKey': api_key,
    'secret': secret,
    'enableRateLimit': True,
})

# 设置测试网 URL
exchange.urls['api'] = {
    'public': 'https://testnet.binance.vision/api/v3',
    'private': 'https://testnet.binance.vision/api/v3',
}

try:
    print("\n[1/3] Fetching server time...")
    time = exchange.fetch_time()
    print(f"[OK] Server time: {time}")
    
    print("\n[2/3] Fetching balance...")
    balance = exchange.fetch_balance()
    print(f"[OK] Balance fetched!")
    usdt = balance.get('USDT', {})
    print(f"    USDT: {usdt.get('free', 0)}")
    
    print("\n[3/3] Fetching BTC/USDT ticker...")
    ticker = exchange.fetch_ticker('BTC/USDT')
    print(f"[OK] BTC Price: ${ticker.get('last', 0):,.2f}")
    
    print("\n" + "=" * 60)
    print("SUCCESS - Binance Vision Testnet working!")
    print("=" * 60)
    
except ccxt.NetworkError as e:
    print(f"\n[ERROR] Network Error: {e}")
except ccxt.AuthenticationError as e:
    print(f"\n[ERROR] Auth Error: {e}")
except Exception as e:
    print(f"\n[ERROR] {type(e).__name__}: {e}")
