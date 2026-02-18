#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""加密货币价格监控脚本 - 妲己财富增长系统"""

import urllib.request
import json
from datetime import datetime

def get_crypto_prices():
    """从 CoinGecko 获取加密货币价格"""
    try:
        url = 'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,binancecoin,solana,cardano&vs_currencies=usd&include_24hr_change=true'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req, timeout=10)
        data = json.loads(response.read())
        
        print("=" * 60)
        print(f"🦊 妲己加密货币监控 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        coins = {
            'bitcoin': ('BTC', '比特币'),
            'ethereum': ('ETH', '以太坊'),
            'binancecoin': ('BNB', '币安币'),
            'solana': ('SOL', '索拉纳'),
            'cardano': ('ADA', '卡尔达诺')
        }
        
        for coin_id, (symbol, name) in coins.items():
            if coin_id in data:
                price = data[coin_id]['usd']
                change = data[coin_id].get('usd_24h_change', 0)
                change_str = f"+{change:.2f}%" if change >= 0 else f"{change:.2f}%"
                print(f"{symbol} {name}: ${price:,} (24h: {change_str})")
        
        print("=" * 60)
        return data
    except Exception as e:
        print(f"获取价格失败：{e}")
        return None

if __name__ == '__main__':
    get_crypto_prices()
