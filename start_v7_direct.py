#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v7.2 直连启动脚本 - 完全绕过系统代理
使用 OKX IP 直连 + Host header
"""

# 第 1 步：在导入任何库之前清除代理环境变量
import os
import sys

print("=" * 60)
print("Web3Million v7.2 - 直连启动")
print("=" * 60)

# 清除所有代理相关环境变量
proxy_keys = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'NO_PROXY']
for key in proxy_keys:
    if key in os.environ:
        del os.environ[key]
        print(f"[OK] 清除环境变量：{key}")

print()

# 第 2 步：导入必要库
import socket
import requests
import urllib3
urllib3.disable_warnings()

# 第 3 步：猴子补丁 - 强制 DNS 解析到 OKX IP
OKX_IP = '43.199.3.187'
original_getaddrinfo = socket.getaddrinfo

def patched_getaddrinfo(*args, **kwargs):
    host = args[0]
    if 'okx.com' in host.lower():
        print(f"[OK] DNS 劫持：{host} -> {OKX_IP}")
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', (OKX_IP, args[1]))]
    return original_getaddrinfo(*args, **kwargs)

socket.getaddrinfo = patched_getaddrinfo

# 第 4 步：创建无代理 Session
class NoProxySession(requests.Session):
    def __init__(self):
        super().__init__()
        self.trust_env = False
        self.proxies = {}
        self.verify = False
        print("[OK] 创建无代理 Session")

# 替换默认 Session
requests.Session = NoProxySession

# 第 5 步：导入 ccxt 并配置
import ccxt

print()
print("初始化 OKX 测试网...")

okx = ccxt.okx({
    'apiKey': '',
    'secret': '',
    'password': '',
    'enableRateLimit': True,
})
okx.set_sandbox_mode(True)

# 强制使用 IP
okx.hostname = OKX_IP
okx.urls['api']['rest'] = f'https://{OKX_IP}'
okx.urls['test']['rest'] = f'https://{OKX_IP}'
okx.headers['Host'] = 'www.okx.com'

# 确保使用无代理 session
okx.session = NoProxySession()

print(f"[OK] OKX 配置完成 (hostname={okx.hostname})")
print()

# 第 6 步：测试连接
print("测试连接 OKX...")
try:
    ticker = okx.fetch_ticker('BTC/USDT:USDT')
    print(f"[OK] 连接成功！BTC: ${ticker['last']}")
except Exception as e:
    print(f"[FAIL] 连接失败：{e}")
    sys.exit(1)

print()
print("=" * 60)
print("启动 v7.2 交易员...")
print("=" * 60)
print()

# 第 7 步：运行 v7.2 交易员
exec(open('perp_trader_v7_2.py', encoding='utf-8').read())
