#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v7.2 启动脚本 - 强制禁用代理
"""
import os
import sys

# 清除所有代理环境变量
for key in list(os.environ.keys()):
    if 'proxy' in key.lower():
        del os.environ[key]
os.environ['NO_PROXY'] = '*'

# 在导入 ccxt 之前先配置 requests
import requests
from requests import Session
from requests.adapters import HTTPAdapter

# 创建不使用代理的 Session 类
class NoProxySession(Session):
    def __init__(self):
        super().__init__()
        self.trust_env = False
        self.proxies = {}

# 替换默认的 Session
requests.Session = NoProxySession

# 现在导入 ccxt
import ccxt
from ccxt.base.exchange import Exchange

# 创建 OKX 实例
okx = ccxt.okx({
    'apiKey': '',
    'secret': '',
    'password': '',
    'enableRateLimit': True,
})
okx.set_sandbox_mode(True)

# 确保不使用代理
okx.session = NoProxySession()

print("测试连接 OKX...")
try:
    # 测试获取 ticker
    ticker = okx.fetch_ticker('BTC/USDT:USDT')
    print(f"✅ 成功！BTC: ${ticker['last']}")
except Exception as e:
    print(f"❌ 失败：{str(e)[:200]}")
    sys.exit(1)

print("\n启动 v7.2 交易员...")
exec(open('perp_trader_v7_2.py', encoding='utf-8').read())
