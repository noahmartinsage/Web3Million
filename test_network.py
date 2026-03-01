#!/usr/bin/env python3
"""Test network connectivity"""
import requests
import time

urls = [
    ('Google', 'https://www.google.com'),
    ('OKX', 'https://www.okx.com'),
    ('Binance', 'https://testnet.binancefuture.com'),
    ('Cloudflare', 'https://www.cloudflare.com'),
]

for name, url in urls:
    try:
        start = time.time()
        r = requests.get(url, timeout=10)
        elapsed = time.time() - start
        print(f"✓ {name}: {r.status_code} ({elapsed:.2f}s)")
    except Exception as e:
        print(f"✗ {name}: {type(e).__name__}")
