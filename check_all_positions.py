import ccxt

ex = ccxt.okx({
    'apiKey': 'b71ee824-5524-4cde-b818-b8e294c27d56',
    'secret': '76122A8879980469F474F042135584DB',
    'password': 'Qian159.',
    'testnet': True,
    'options': {'defaultType': 'swap'}
})

# Check all positions
positions = ex.fetch_positions()
print('=== All Positions ===')
has_position = False
for p in positions:
    size = p.get('size', 0)
    if size != 0:
        has_position = True
        print(f'Symbol: {p["symbol"]}')
        print(f'Side: {p["side"]}')
        print(f'Size: {size}')
        print(f'Entry Price: {p["entryPrice"]}')
        print(f'Mark Price: {p.get("markPrice", "N/A")}')
        print(f'Unrealized PnL: {p.get("unrealizedPnl", "N/A")}')
        print(f'Leverage: {p.get("leverage", "N/A")}x')
        print('---')

if not has_position:
    print('No positions')

bal = ex.fetch_balance()
print(f'\nUSDT Balance: {bal["total"].get("USDT", 0)}')
