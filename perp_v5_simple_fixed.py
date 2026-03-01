# Import necessary libraries
import ccxt
import pandas as pd
import numpy as np
import time
from datetime import datetime

class PerpetualTraderV5:
    def __init__(self):
        # Initialize the OKX exchange with testnet settings
        self.exchange = ccxt.okx(
            apiKey='b71ee824-5524-4cde-b818-b8e294c27d56',
            secret='76122A8879980469F474F042135584DB',
            password='Qian159.',
            testnet=True,
            options={'defaultType': 'swap'}
        )

def main():
    trader = PerpetualTraderV5()
    trader.exchange.load_markets()
    print(f'✅ OKX 市场数据加载成功
')

    # 获取当前价格
    btc_price = trader.exchange.fetch_ticker('BTC/USDT:USDT')['last']
    eth_price = trader.exchange.fetch_ticker('ETH/USDT:USDT')['last']

    print(f'BTC 价格: {btc_price}
ETH 价格: {eth_price}
')

if __name__ == '__main__':
    main()