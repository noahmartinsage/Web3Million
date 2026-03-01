#!/usr/bin/env python3
"""Test China domestic network"""
import requests
import time

urls = [
    ('Baidu', 'https://www.baidu.com'),
    ('163', 'https://www.163.com'),
    ('QQ', 'https://www.qq.com'),
    ('Localhost', 'http://127.0.0.1'),
]

for name, url in urls:
    try:
        start = time.time()
        r = requests.get(url, timeout=10)
        elapsed = time.time() - start
        print(f"OK {name}: {r.status_code} ({elapsed:.2f}s)")
    except Exception as e:
        print(f"FAIL {name}: {type(e).__name__}")
