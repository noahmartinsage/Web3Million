#!/usr/bin/env python3
# -*- coding: utf-8- -*-
"""检查测试网状态"""
import ccxt
import json

print('=' * 60)
print('Web3Million 测试网状态检查')
print('=' * 60)

# 连接 OKX 测试网
exchange = ccxt.okx({
    'apiKey': 'b71ee824-5524-4cde-b818-b8e294c27d56',
    'secret': '76122A8879980469F474F042135584DB',
    'password': 'Qian159.',
    'testnet': True
})

try:
    # 获取市场价格
    ticker = exchange.fetch_ticker('ETH/USDT')
    print(f'\n当前价格：{ticker["last"]} USDT')
    print(f'24h 涨跌：{ticker["percentage"]}%')
    
    # 获取账户余额
    balance = exchange.fetch_balance()
    usdt = balance['total'].get('USDT', 0)
    eth = balance['total'].get('ETH', 0)
    
    print(f'\n账户余额:')
    print(f'  USDT: {usdt}')
    print(f'  ETH: {eth}')
    
    # 计算总价值
    total_value = usdt + (eth * ticker['last'])
    print(f'\n总资产价值：${total_value:.2f} USDT')
    
    print('\n[OK] 测试网连接正常')
    print('=' * 60)
    
except Exception as e:
    print(f'\n[ERROR] 错误：{e}')
