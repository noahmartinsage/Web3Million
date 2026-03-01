import ccxt
from datetime import datetime

print("=" * 60)
print(f"[MARKET DATA] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)

try:
    # Try Binance (spot market - more reliable)
    exchange = ccxt.binance()
    symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
    
    for symbol in symbols:
        ticker = exchange.fetch_ticker(symbol)
        change = ticker.get('percentage', 0)
        direction = "UP" if change >= 0 else "DOWN"
        
        print(f"\n{symbol}")
        print(f"  Price: USD {ticker['last']:,.2f}")
        print(f"  24h: {direction} {change:+.2f}%")
        print(f"  High: {ticker['high']:,.2f} | Low: {ticker['low']:,.2f}")
        print(f"  Volume: {ticker['quoteVolume']:,.0f} USDT")
    
    print("\n" + "=" * 60)
    print("[OK] Market data fetched successfully!")
except Exception as e:
    print(f"[ERROR] {e}")
    print("\nTrying OKX testnet...")
    
    try:
        exchange2 = ccxt.okx({
            'testnet': True,
            'options': {'defaultType': 'swap'}
        })
        for symbol in ['BTC/USDT:USDT', 'ETH/USDT:USDT']:
            ticker = exchange2.fetch_ticker(symbol)
            print(f"{symbol}: ${ticker['last']:,.2f}")
        print("[OK] OKX testnet working!")
    except Exception as e2:
        print(f"[ERROR] OKX also failed: {e2}")
