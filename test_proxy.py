#!/usr/bin/env python3
"""Test proxy connectivity"""
import requests

proxies = {
    'http': 'http://127.0.0.1:7890',
    'https': 'http://127.0.0.1:7890',
}

try:
    r = requests.get('https://www.baidu.com', proxies=proxies, timeout=10)
    print(f"OK Proxy works: {r.status_code}")
except Exception as e:
    print(f"FAIL Proxy error: {e}")
