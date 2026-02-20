import ccxt
import pandas as pd
import time
import sys

e = ccxt.okx({
    'apiKey': 'b71ee824-5524-4cde-b818-b8e294c27d56',
    'secret': '76122A8879980469F474F042135584DB',
    'password': 'Qian159.',
    'testnet': True
})

symbol = 'ETH/USDT'

sys.stdout.write('Starting HF trading...\n')
sys.stdout.flush()

for i in range(20):
    try:
        price = e.fetch_ticker(symbol)['last']
        b = e.fetch_balance()
        usdt = b['total'].get('USDT', 0)
        eth = b['total'].get('ETH', 0)
        
        ohlcv = e.fetch_ohlcv(symbol, '5m', limit=30)
        df = pd.DataFrame(ohlcv, columns=['t','o','h','l','c','v'])
        
        # Simple MA signal
        ma5 = df['c'].rolling(5).mean().iloc[-1]
        ma20 = df['c'].rolling(20).mean().iloc[-1]
        
        if ma5 > ma20:
            signal = 'LONG'
        elif ma5 < ma20:
            signal = 'SHORT'
        else:
            signal = 'NEUTRAL'
        
        total = usdt + eth * price
        
        msg = f'[{i}] {signal} | ${price:.0} | Total: ${total:.0} | USDT:{usdt:.0} ETH:{eth:.3}'
        sys.stdout.write(msg + '\n')
        sys.stdout.flush()
        
        time.sleep(20)
        
    except Exception as ex:
        sys.stdout.write(f'Error: {ex}\n')
        sys.stdout.flush()

sys.stdout.write('Done\n')
sys.stdout.flush()
