import ccxt

ex = ccxt.okx({
    'apiKey': 'b71ee824-5524-4cde-b818-b8e294c27d56',
    'secret': '76122A8879980469F474F042135584DB',
    'password': 'Qian159.',
    'testnet': True,
    'options': {'defaultType': 'swap'}
})

# Check positions
positions = ex.fetch_positions(['ETH/USDT:USDT'])
print('=== ETH/USDT Positions ===')
for p in positions:
    if p.get('size', 0) != 0:
        print('Side:', p['side'])
        print('Size:', p['size'])
        print('Entry:', p['entryPrice'])
        print('Current:', p.get('markPrice', 'N/A'))
        print('Unrealized PnL:', p['unrealizedPnl'])
        print('Leverage:', p.get('leverage', 'N/A'), 'x')

# Check balance
bal = ex.fetch_balance()
print('\nUSDT Balance:', bal['total'].get('USDT', 0))
