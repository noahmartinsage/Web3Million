#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v7.2 启动脚本 - 使用 IP 直连绕过代理
"""
import os
import sys
import socket

# 清除代理环境变量
for key in list(os.environ.keys()):
    if 'proxy' in key.lower():
        del os.environ[key]

# 导入 requests 并配置
import requests
import urllib3
urllib3.disable_warnings()

# 现在导入 ccxt
import ccxt

# 创建 OKX 实例
okx = ccxt.okx({
    'apiKey': '',
    'secret': '',
    'password': '',
    'enableRateLimit': True,
})
okx.set_sandbox_mode(True)

# 强制使用无代理 session
okx.session.trust_env = False
okx.session.proxies = {}
okx.session.verify = False

# 修改 hosts 解析 - 直接解析到 IP
original_getaddrinfo = socket.getaddrinfo
def patched_getaddrinfo(*args, **kwargs):
    host = args[0]
    if 'okx.com' in host:
        # 返回 OKX 的 IP 地址
        return [
            (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('43.199.3.187', args[1])),
        ]
    return original_getaddrinfo(*args, **kwargs)

socket.getaddrinfo = patched_getaddrinfo

print("测试连接 OKX...")
try:
    ticker = okx.fetch_ticker('BTC/USDT:USDT')
    print(f"✅ 成功！BTC: ${ticker['last']}")
except Exception as e:
    print(f"❌ 失败：{str(e)[:200]}")
    sys.exit(1)

print("\n启动 v7.2 交易员...")
exec(open('perp_trader_v7_2.py', encoding='utf-8').read())
