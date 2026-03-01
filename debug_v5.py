import ccxt
import pandas as pd
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

print('=== Debugging v5 System ===')
print('1. Loading market...')
ex.load_markets()
print('   OK')

print('2. Getting ticker...')
ticker = ex.fetch_ticker(symbol)
price = ticker['last']
print(f'   Price: ${price}')

print('3. Setting leverage...')
try:
    ex.set_leverage(50, symbol)
    print('   OK')
except Exception as e:
    print(f'   Error: {e}')

print('4. Fetching OHLCV...')
ohlcv = ex.fetch_ohlcv(symbol, '15m', limit=50)
print(f'   Got {len(ohlcv)} candles')

print('5. Calculating indicators...')
df = pd.DataFrame(ohlcv, columns=['t','o','h','l','c','v'])
closes = df['c']

# RSI
delta = closes.diff()
gain = delta.where(delta > 0, 0).rolling(14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
rs = gain / loss
df['rsi'] = 100 - (100 / (1 + rs))

# MACD
ema12 = closes.ewm(span=12).mean()
ema26 = closes.ewm(span=26).mean()
df['macd'] = ema12 - ema26
df['macd_signal'] = df['macd'].ewm(span=9).mean()
df['macd_hist'] = df['macd'] - df['macd_signal']

# MA
df['ma5'] = closes.rolling(5).mean()
df['ma20'] = closes.rolling(20).mean()

latest = df.iloc[-1]
prev = df.iloc[-2]

print(f'   RSI: {latest["rsi"]:.1f}')
print(f'   MACD Hist: {latest["macd_hist"]:.4f}')
print(f'   MA5 > MA20: {latest["ma5"] > latest["ma20"]}')

print('6. Generating signal...')
rsi = latest['rsi']
macd_hist = latest['macd_hist']
macd_hist_prev = prev['macd_hist']
ma_trend = 1 if latest['ma5'] > latest['ma20'] else -1

if rsi <= 35 and macd_hist > macd_hist_prev and ma_trend > 0:
    signal = 'LONG'
elif rsi >= 65 and macd_hist < macd_hist_prev and ma_trend < 0:
    signal = 'SHORT'
else:
    signal = 'NEUTRAL'

print(f'   Signal: {signal}')

print('\n=== All checks passed! ===')
