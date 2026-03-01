import ccxt
from datetime import datetime

exchange = ccxt.okx()
symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT']

print("=" * 60)
print(f"[MARKET] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)

for symbol in symbols:
    ticker = exchange.fetch_ticker(symbol)
    change_pct = ticker.get('percentage', 0)
    change_symbol = "UP" if change_pct >= 0 else "DOWN"
    
    print(f"\n{symbol}")
    print(f"  Price: ${ticker['last']:,.2f}")
    print(f"  24h Change: {change_symbol} {change_pct:+.2f}%")
    print(f"  24h High: ${ticker['high']:,.2f}")
    print(f"  24h Low: ${ticker['low']:,.2f}")
    print(f"  24h Volume: ${ticker['quoteVolume']:,.0f} USDT")

print("\n" + "=" * 60)
