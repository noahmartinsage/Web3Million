import ccxt

class PerpetualTraderV5:
    def __init__(self):
        self.exchange = ccxt.okx({
            'apiKey': 'b71ee824-5524-4cde-b818-b8e294c27d56',
            'secret': '76122A8879980469F474F042135584DB',
            'password': 'Qian159.',
            'testnet': True,
            'options': {'defaultType': 'swap'}
        })

def main():
    trader = PerpetualTraderV5()
    trader.exchange.load_markets()
    print('OKX markets loaded')

    btc = trader.exchange.fetch_ticker('BTC/USDT:USDT')['last']
    eth = trader.exchange.fetch_ticker('ETH/USDT:USDT')['last']
    sol = trader.exchange.fetch_ticker('SOL/USDT:USDT')['last']

    print('BTC:', btc)
    print('ETH:', eth)
    print('SOL:', sol)

    bal = trader.exchange.fetch_balance()
    print('USDT:', bal['total'].get('USDT', 0))

if __name__ == '__main__':
    main()
