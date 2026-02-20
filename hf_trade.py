import ccxt
import pandas as pd
import time

e = ccxt.okx({
    'apiKey': 'b71ee824-5524-4cde-b818-b8e294c27d56',
    'secret': '76122A8879980469F474F042135584DB',
    'password': 'Qian159.',
    'testnet': True
})

symbol = 'ETH/USDT'
position = None
entry_price = 0

def get_signal():
    ohlcv = e.fetch_ohlcv(symbol, '5m', limit=50)
    df = pd.DataFrame(ohlcv, columns=['t','o','h','l','c','v'])
    
    # RSI
    delta = df['c'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rsi = 100 - (100 / (1 + gain / loss))
    
    # MACD
    ema12 = df['c'].ewm(span=12).mean()
    ema26 = df['c'].ewm(span=26).mean()
    macd = ema12 - ema26
    macd_sig = macd.ewm(span=9).mean()
    macd_hist = macd - macd_sig
    
    # MA
    ma5 = df['c'].rolling(5).mean()
    ma20 = df['c'].rolling(20).mean()
    
    latest = df.iloc[-1]
    
    if latest['c'] > ma5.iloc[-1] and macd_hist.iloc[-1] > 0 and rsi.iloc[-1] < 65:
        return 'LONG'
    elif latest['c'] < ma5.iloc[-1] and macd_hist.iloc[-1] < 0 and rsi.iloc[-1] > 35:
        return 'SHORT'
    return 'NEUTRAL'

print('Starting HF trading...')
for i in range(30):
    try:
        price = e.fetch_ticker(symbol)['last']
        b = e.fetch_balance()
        usdt = b['total'].get('USDT', 0)
        eth = b['total'].get('ETH', 0)
        
        signal = get_signal()
        
        # Check exit
        if position == 'LONG':
            pnl_pct = (price - entry_price) / entry_price
            if pnl_pct >= 0.03 or pnl_pct <= -0.015:
                e.create_market_sell_order(symbol, eth)
                print(f'[{i}] CLOSE LONG @ {price}, PnL: {pnl_pct*100:.1f}%')
                position = None
        elif position == 'SHORT':
            pnl_pct = (entry_price - price) / entry_price
            if pnl_pct >= 0.03 or pnl_pct <= -0.015:
                e.create_market_buy_order(symbol, eth)
                print(f'[{i}] CLOSE SHORT @ {price}, PnL: {pnl_pct*100:.1f}%')
                position = None
        
        # Open position
        if not position and signal != 'NEUTRAL':
            amount = (usdt * 0.1) / price
            if signal == 'LONG':
                e.create_market_buy_order(symbol, amount)
                entry_price = price
                position = 'LONG'
                print(f'[{i}] OPEN LONG {amount:.4f} @ {price}')
            else:
                e.create_market_sell_order(symbol, amount)
                entry_price = price
                position = 'SHORT'
                print(f'[{i}] OPEN SHORT {amount:.4f} @ {price}')
        
        total = usdt + eth * price
        print(f'[{i}] {signal} | Price: {price} | Total: {total:.0} | Position: {position}')
        
        time.sleep(15)
    except Exception as ex:
        print(f'Error: {ex}')
        time.sleep(5)

print('Done')
