import ccxt
exchange = ccxt.okx({
    'apiKey': 'b71ee824-5524-4cde-b818-b8e294c27d56',
    'secret': '76122A8879980469F474F042135584DB',
    'password': 'Qian159.',
    'testnet': True
})

symbol = 'ETH/USDT'
balance = exchange.fetch_balance()
usdt = balance['total'].get('USDT', 0)
print('Current USDT:', usdt)

# Calculate position size (10% of capital)
position_value = usdt * 0.1
current_price = exchange.fetch_ticker(symbol)['last']
amount = position_value / current_price

print('Price:', current_price)
print('Position size:', amount, 'ETH')

# Execute buy order
order = exchange.create_market_buy_order(symbol, amount)
print('Order ID:', order['id'])
print('Status:', order['status'])
print('Amount:', order['amount'])
print('Price:', order['price'])
print('Trade executed successfully!')
