#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查 Web3Million v7.2 交易状态"""

import ccxt
import json
import sys

try:
    # 加载配置
    with open('okx_config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 初始化 OKX 测试网
    exchange = ccxt.okx({
        'apiKey': config['api_key'],
        'secret': config['secret_key'],
        'password': config['passphrase'],
        'enableRateLimit': True,
        'options': {'defaultType': 'swap'},
    })
    exchange.set_sandbox_mode(True)
    
    # 获取账户余额
    balance = exchange.fetch_balance()
    usdt_balance = balance['total'].get('USDT', 0)
    
    # 获取持仓
    positions = exchange.fetch_positions()
    
    # 过滤有值的持仓
    active_positions = []
    total_unrealized_pnl = 0
    for pos in positions:
        if pos['contracts'] and pos['contracts'] > 0:
            active_positions.append({
                'symbol': pos['symbol'],
                'side': pos['side'],
                'contracts': pos['contracts'],
                'entryPrice': pos['entryPrice'],
                'markPrice': pos['markPrice'],
                'unrealizedPnl': pos['unrealizedPnl'],
                'percentage': pos['percentage']
            })
            total_unrealized_pnl += pos['unrealizedPnl'] if pos['unrealizedPnl'] else 0
    
    # 输出结果
    print("=" * 60)
    print("Web3Million v7.2 交易状态报告")
    print("=" * 60)
    print(f"时间：{exchange.iso8601(exchange.milliseconds())}")
    print(f"账户余额：{usdt_balance:.2f} USDT")
    print(f"未实现盈亏：{total_unrealized_pnl:.2f} USDT")
    print(f"活跃持仓数：{len(active_positions)}")
    print()
    
    if active_positions:
        print("持仓详情:")
        for pos in active_positions:
            print(f"  {pos['symbol']} {pos['side']}:")
            print(f"    数量：{pos['contracts']}")
            print(f"    入场价：{pos['entryPrice']}")
            print(f"    标记价：{pos['markPrice']}")
            print(f"    未实现盈亏：{pos['unrealizedPnl']:.2f} USDT ({pos['percentage']*100:.2f}%)")
    else:
        print("无活跃持仓")
    
    print("=" * 60)
    
except Exception as e:
    print(f"错误：{e}")
    sys.exit(1)
