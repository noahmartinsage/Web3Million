#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v7.2 终极直连脚本 - 完全接管 ccxt 的请求
"""

import os
import sys

# 清除代理环境变量
for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'NO_PROXY']:
    if key in os.environ:
        del os.environ[key]

print("=" * 60)
print("Web3Million v7.2 - 终极直连")
print("=" * 60)

import socket
import requests
import urllib3
urllib3.disable_warnings()

# DNS 劫持
OKX_IP = '43.199.3.187'
original_getaddrinfo = socket.getaddrinfo
def patched_getaddrinfo(*args, **kwargs):
    host = args[0]
    if 'okx.com' in host.lower():
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', (OKX_IP, args[1]))]
    return original_getaddrinfo(*args, **kwargs)
socket.getaddrinfo = patched_getaddrinfo

# 创建全局无代理 session
global_session = requests.Session()
global_session.trust_env = False
global_session.proxies = {}
global_session.verify = False
global_session.headers.update({'Host': 'www.okx.com'})

print("[OK] 创建全局无代理 session")

# 导入 ccxt
import ccxt

# 创建 OKX 实例
okx = ccxt.okx({
    'apiKey': '',
    'secret': '',
    'password': '',
    'enableRateLimit': True,
})
okx.set_sandbox_mode(True)

# 完全替换 session
okx.session = global_session
okx.hostname = OKX_IP

print("[OK] OKX 初始化完成")
print()
print("测试连接...")

# 直接使用 session 测试
try:
    url = f'https://{OKX_IP}/api/v5/market/tickers?instType=SWAP'
    r = global_session.get(url, timeout=10)
    data = r.json()
    if data.get('code') == '0':
        btc = next((x for x in data['data'] if 'BTC' in x['instId']), None)
        if btc:
            print(f"[OK] 直连成功！BTC: ${float(btc['last']):.2f}")
    else:
        print(f"[FAIL] API 返回错误：{data}")
        sys.exit(1)
except Exception as e:
    print(f"[FAIL] 连接失败：{e}")
    sys.exit(1)

print()
print("=" * 60)
print("启动 v7.2 交易员...")
print("=" * 60)
print()

# 修改 perp_trader_v7_2.py 使用我们的 session
exec(open('perp_trader_v7_2.py', encoding='utf-8').read())
