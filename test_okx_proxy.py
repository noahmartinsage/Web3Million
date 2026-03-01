#!/usr/bin/env python3
"""Test OKX with proxy"""
import ccxt
import sys

print("Testing OKX Testnet with proxy...")

proxies = {
    'http': 'http://127.0.0.1:7890',
    'https': 'http://127.0.0.1:7890',
}

exchange = ccxt.okx({
    'apiKey': 'b71ee824-5524-4cde-b818-b8e294c27d56',
    'secret': '76122A8879980469F474F042135584DB',
    'password': 'Qian159.',
    'proxies': proxies,
    'timeout': 30000,
})

exchange.sandbox = True

try:
    print("Fetching BTC ticker...")
    ticker = exchange.fetch_ticker('BTC/USDT:USDT')
    print(f"OK BTC Price: ${ticker.get('last', 'N/A')}")
    
    print("Fetching balance...")
    balance = exchange.fetch_balance()
    usdt = balance.get('USDT', {})
    print(f"OK USDT Balance: {usdt.get('free', 'N/A')}")
    
    print("\nOK Connection successful with proxy!")
except ccxt.NetworkError as e:
    print(f"FAIL Network Error: {e}")
except ccxt.AuthenticationError as e:
    print(f"FAIL Auth Error: {e}")
except Exception as e:
    print(f"FAIL Error: {type(e).__name__}: {e}")
