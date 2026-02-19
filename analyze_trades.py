import ccxt

e = ccxt.okx({
    'apiKey': 'b71ee824-5524-4cde-b818-b8e294c27d56',
    'secret': '76122A8879980469F474F042135584DB',
    'password': 'Qian159.',
    'testnet': True
})

orders = e.fetch_closed_orders('ETH/USDT', limit=20)

print('='*60)
print('TRADE LIST ANALYSIS')
print('='*60)

trades = []
for i in range(0, len(orders), 2):
    if i+1 < len(orders):
        buy = orders[i]
        sell = orders[i+1]
        if buy['side'] == 'buy' and sell['side'] == 'sell':
            pnl = (sell['price'] - buy['price']) * buy['amount']
            pnl_pct = (sell['price'] - buy['price']) / buy['price'] * 100
            print(f'#{len(trades)+1} BUY {buy["amount"]} @ {buy["price"]:.2f} -> SELL @ {sell["price"]:.2f} | PnL: ${pnl:.2f} ({pnl_pct:+.2f}%)')
            trades.append({'buy': buy, 'sell': sell, 'pnl': pnl, 'pnl_pct': pnl_pct})

print('='*60)
total_pnl = sum(t['pnl'] for t in trades)
print(f'Total PnL: ${total_pnl:.2f}')
print(f'Total Trades: {len(trades)}')
wins = [t for t in trades if t['pnl'] > 0]
print(f'Win Rate: {len(wins)/len(trades)*100:.1f}%' if trades else 'No trades')
