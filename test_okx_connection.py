#!/usr/bin/env python3
"""Test OKX Testnet Connection"""
import ccxt

print("Testing OKX Testnet connection...")

exchange = ccxt.okx({
    'apiKey': 'b71ee824-5524-4cde-b818-b8e294c27d56',
    'secret': '76122A8879980469F474F042135584DB',
    'password': 'Qian159.',
    'enableRateLimit': True,
})

# Enable sandbox mode for testnet
exchange.sandbox = True

print(f"API URLs: {exchange.urls}")

try:
    print("Loading markets...")
    exchange.load_markets()
    print("✓ Markets loaded!")
    
    print("Fetching balance...")
    balance = exchange.fetch_balance()
    print(f"✓ Balance: {balance}")
    
    print("\n✓ OKX Testnet connection successful!")
except Exception as e:
    print(f"✗ Error: {e}")
