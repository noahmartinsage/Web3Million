import ccxt
from datetime import datetime

print("=" * 60)
print(f"[MARKET WAR REPORT] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)

try:
    # Try Binance first (usually more reliable)
    exchange = ccxt.binanceusdm()
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
except Exception as e:
    print(f"Error fetching data: {e}")
    print("Trying alternative...")
    
    # Fallback to OKX public API
    exchange2 = ccxt.okx()
    for symbol in ['BTC/USDT:USDT', 'ETH/USDT:USDT']:
        try:
            ticker = exchange2.fetch_ticker(symbol)
            print(f"{symbol}: ${ticker['last']:,.2f}")
        except:
            print(f"{symbol}: Data unavailable")
