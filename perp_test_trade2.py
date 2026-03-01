import ccxt

ex = ccxt.okx({
    'apiKey': 'b71ee824-5524-4cde-b818-b8e294c27d56',
    'secret': '76122A8879980469F474F042135584DB',
    'password': 'Qian159.',
    'testnet': True,
    'options': {'defaultType': 'swap'},
    'enableRateLimit': True
})

symbol = 'ETH/USDT:USDT'

print('Getting ETH price...')
ticker = ex.fetch_ticker(symbol)
price = ticker['last']
print(f'ETH price: {price}')

# Try different leverage levels
for lev in [10, 20, 30, 50, 75]:
    try:
        ex.set_leverage(lev, symbol)
        print(f'Leverage {lev}x: OK')
    except Exception as e:
        print(f'Leverage {lev}x: FAILED - {e}')
        break

# Use 50x as max
leverage = 50
print(f'\nUsing {leverage}x leverage...')
ex.set_leverage(leverage, symbol)

# Calculate amount: 10U / price
amount = 10 / price
amount = round(amount, 4)
print(f'Position size: {amount} ETH')

print('Placing BUY order...')
try:
    order = ex.create_market_buy_order(symbol, amount)
    print(f'ORDER SUCCESS!')
    print(f'Order ID: {order["id"]}')
    print(f'Status: {order["status"]}')
except Exception as e:
    print(f'Order failed: {e}')
