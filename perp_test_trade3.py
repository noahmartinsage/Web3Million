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

symbol = 'ETH/USDT:USDT'

print('Getting ETH price...')
ticker = ex.fetch_ticker(symbol)
price = ticker['last']
print(f'ETH price: {price}')

# Use 50x leverage
leverage = 50
print(f'Setting leverage to {leverage}x...')
ex.set_leverage(leverage, symbol)

# Calculate amount: min 0.01 ETH = ~$20 at current price
amount = 0.01  # Minimum order size
usd_value = amount * price
print(f'Position: {amount} ETH = ${usd_value:.2}')

print('Placing LONG order (50x leverage)...')
try:
    order = ex.create_market_buy_order(symbol, amount)
    print('ORDER SUCCESS!')
    print(f'Order ID: {order["id"]}')
except Exception as e:
    print(f'Order failed: {e}')

# Wait a bit and check position
print('\nChecking position...')
time.sleep(2)

positions = ex.fetch_positions([symbol])
for p in positions:
    if p.get('size', 0) != 0:
        print(f'Position: {p["side"]} {p["size"]} contracts')
        print(f'Entry price: {p["entryPrice"]}')
        print(f'Unrealized PnL: {p["unrealizedPnl"]}')

print('\nDone!')
