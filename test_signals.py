import ccxt
import pandas as pd

ex = ccxt.okx({
    'apiKey': 'b71ee824-5524-4cde-b818-b8e294c27d56',
    'secret': '76122A8879980469F474F042135584DB',
    'password': 'Qian159.',
    'testnet': True,
    'options': {'defaultType': 'swap'},
    'enableRateLimit': True
})

print('Loading markets...')
ex.load_markets()
print('Markets loaded')

symbols = ['ETH/USDT:USDT', 'BTC/USDT:USDT', 'SOL/USDT:USDT']

for symbol in symbols:
    print(f'Checking {symbol}...')
    try:
        ohlcv = ex.fetch_ohlcv(symbol, '15m', limit=50)
        df = pd.DataFrame(ohlcv, columns=['t','o','h','l','c','v'])
        closes = df['c']
        
        # RSI
        delta = closes.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1]
        
        # MACD
        ema12 = closes.ewm(span=12).mean()
        ema26 = closes.ewm(span=26).mean()
        macd = ema12 - ema26
        macd_signal = macd.ewm(span=9).mean()
        macd_hist = (macd - macd_signal).iloc[-1]
        
        # MA
        ma5 = closes.rolling(5).mean().iloc[-1]
        ma20 = closes.rolling(20).mean().iloc[-1]
        
        price = closes.iloc[-1]
        
        print(f'  Price: ${price:.2}, RSI: {rsi:.1f}, MACD: {macd_hist:.2f}, MA5>MA20: {ma5>ma20}')
        
    except Exception as e:
        print(f'  Error: {e}')

print('Done!')
