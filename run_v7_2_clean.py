#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""启动 v7.2 - 在导入任何库之前清除代理"""

# 必须在导入其他库之前清除代理！
import os
for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    if key in os.environ:
        del os.environ[key]
os.environ['NO_PROXY'] = '*'

# 现在导入其他库
import ccxt
import urllib3
urllib3.disable_warnings()

print("代理已清除，测试连接...")

okx = ccxt.okx({'enableRateLimit': True})
okx.set_sandbox_mode(True)
okx.session.trust_env = False
okx.session.proxies = {}
okx.session.verify = False
okx.hostname = '43.199.3.187'
okx.headers['Host'] = 'www.okx.com'

try:
    ticker = okx.fetch_ticker('BTC/USDT:USDT')
    print(f"成功！BTC: ${ticker['last']}")
    print("\n启动 v7.2 交易员...")
    exec(open('perp_trader_v7_2.py', encoding='utf-8').read())
except Exception as e:
    print(f"失败：{e}")
