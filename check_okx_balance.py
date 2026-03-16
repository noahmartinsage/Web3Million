#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check OKX Testnet Balance"""
import ccxt

exchange = ccxt.okx({
    'apiKey': 'b71ee824-5524-4cde-b818-b8e294c27d56',
    'secret': '76122A8879980469F474F042135584DB',
    'password': 'Qian159.',
    'testnet': True,
    'enableRateLimit': True,
})

try:
    balance = exchange.fetch_balance()
    usdt_balance = balance['total'].get('USDT', 0)
    print(f"OKX Testnet Balance: {usdt_balance} USDT")
    print(f"Available: {balance['free'].get('USDT', 0)} USDT")
    print(f"Used: {balance['used'].get('USDT', 0)} USDT")
except Exception as e:
    print(f"Error: {e}")
