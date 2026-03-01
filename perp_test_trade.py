import ccxt
import time

ex = ccxt.okx({
    'apiKey': 'b71ee824-5524-4cde-b818-b8e294c27d56',
    'secret': '76122A8879980469F474F042135584DB',
    'password': 'Qian159.',
    'testnet': True,
    'options': {'defaultType': 'swap'},
    'enableRateLimit': True
})

print('Loading markets...')
# Don't load all markets, just use symbol directly
symbol = 'ETH/USDT:USDT'

print('Getting ticker...')
ticker = ex.fetch_ticker(symbol)
print(f'ETH price: {ticker["last"]}')

print('Setting leverage...')
ex.set_leverage(125, symbol)

print('Calculating position: 10U / 2018 = 0.00495 ETH')
amount = 10 / 2018
amount = round(amount, 4)
print(f'Amount: {amount}')

print('Placing BUY order...')
try:
    order = ex.create_market_buy_order(symbol, amount)
    print(f'Order ID: {order["id"]}')
    print(f'Status: {order["status"]}')
    print('ORDER SUCCESS!')
except Exception as e:
    print(f'Error: {e}')

print('Done')
