#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复代理问题并启动 v7.2
"""
import os
import sys
import requests
import urllib3

# 禁用所有代理
os.environ['NO_PROXY'] = '*'
for key in list(os.environ.keys()):
    if 'proxy' in key.lower():
        del os.environ[key]

# 禁用警告
urllib3.disable_warnings()

# 强制 requests 不使用代理
requests.adapters.DEFAULT_POOLMANAGER = type('NoProxyPoolManager', (), {
    '__init__': lambda self: None,
    'request': lambda self, *args, **kwargs: None
})

# 现在导入 ccxt
import ccxt

# 创建 OKX 实例
okx = ccxt.okx({
    'apiKey': '',
    'secret': '',
    'password': '',
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})
okx.set_sandbox_mode(True)

# 强制禁用代理
okx.session.trust_env = False
okx.session.proxies = {
    'http': None,
    'https': None,
    'no_proxy': '*'
}

# 测试连接
try:
    ticker = okx.fetch_ticker('BTC/USDT:USDT')
    print(f"✅ OKX 连接成功！BTC 价格：${ticker['last']}")
except Exception as e:
    print(f"❌ 连接失败：{e}")
    sys.exit(1)

# 运行交易员
print("\n🚀 启动 v7.2 交易员...")
exec(open('perp_trader_v7_2.py', encoding='utf-8').read())
