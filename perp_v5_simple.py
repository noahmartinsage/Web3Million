#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million 永续合约量化交易系统 v5.0 - 简洁版
高杠杆、以小博大、小止损大止盈
"""
import ccxt
import time
from datetime import datetime

# 配置
API_KEY = 'b71ee824-5524-4cde-b818-b8e294c27d56'
API_SECRET = '76122A8879980469F474F042135584DB'
PASSWORD = 'Qian159.'

MAX_POSITION_USDT = 10   # 最大10U
LEVERAGE = 125           # 最大杠杆
STOP_LOSS = 0.015        # 1.5%止损
TAKE_PROFIT = 0.10       # 10%止盈

SYMBOLS = ['ETH/USDT:USDT', 'BTC/USDT:USDT', 'SOL/USDT:USDT']

def get_exchange():
    ex = ccxt.okx({
        'apiKey': API_KEY,
        'secret': API_SECRET,
        'password': PASSWORD,
        'testnet': True
    })
    return ex

def get_signal(ex, symbol):
    """简单信号"""
    try:
        ohlcv = ex.fetch_ohlcv(symbol, '15m', limit=50)
        closes = [c[4] for c in ohlcv]
        
        # RSI
        delta = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        gains = [d if d > 0 else 0 for d in delta]
        losses = [-d if d < 0 else 0 for d in delta]
        avg_gain = sum(gains[-14:]) / 14
        avg_loss = sum(losses[-14:]) / 14
        rs = avg_gain / avg_loss if avg_loss > 0 else 100
        rsi = 100 - (100 / (1 + rs))
        
        # MACD
        ema12 = sum(closes[-12:]) / 12
        ema26 = sum(closes[-26:]) / 26
        macd = ema12 - ema26
        
        price = closes[-1]
        
        # 信号
        if rsi < 35 and macd > 0:
            return 'LONG', price, rsi
        elif rsi > 65 and macd < 0:
            return 'SHORT', price, rsi
        return 'NEUTRAL', price, rsi
    except Exception as e:
        print(f"Signal error: {e}")
        return 'NEUTRAL', 0, 50

def main():
    print("="*50)
    print("Web3Million 永续合约 v5.0 启动")
    print(f"仓位: ≤{MAX_POSITION_USDT}U | 杠杆: {LEVERAGE}x")
    print(f"止损: {STOP_LOSS*100}% | 止盈: {TAKE_PROFIT*100}%")
    print("="*50)
    
    ex = get_exchange()
    
    # 获取余额
    balance = ex.fetch_balance()
    usdt = balance['total'].get('USDT', 0)
    print(f"USDT余额: {usdt}")
    
    position = None
    entry_price = 0
    entry_symbol = None
    
    for i in range(20):
        print(f"\n--- 第{i+1}轮 ---")
        
        # 检查平仓
        if position:
            ticker = ex.fetch_ticker(entry_symbol)
            current = ticker['last']
            
            if position == 'LONG':
                pnl_pct = (current - entry_price) / entry_price
            else:
                pnl_pct = (entry_price - current) / entry_price
            
            print(f"持仓: {position} {entry_symbol.split('/')[0]} @ ${current:.2} ({pnl_pct*100:+.1f}%)")
            
            if pnl_pct <= -STOP_LOSS:
                print(f"🛑 止损!")
                # 平仓逻辑
                position = None
            elif pnl_pct >= TAKE_PROFIT:
                print(f"🎯 止盈!")
                position = None
        
        # 扫描机会
        if not position:
            for symbol in SYMBOLS:
                signal, price, rsi = get_signal(ex, symbol)
                if signal != 'NEUTRAL':
                    print(f"发现信号: {signal} {symbol} @ ${price:.2} RSI:{rsi:.1f}")
                    
                    # 开仓
                    try:
                        ex.set_leverage(LEVERAGE, symbol)
                        amount = MAX_POSITION_USDT / price
                        amount = round(amount, 4)
                        
                        if signal == 'LONG':
                            order = ex.create_market_buy_order(symbol, amount)
                        else:
                            order = ex.create_market_sell_order(symbol, amount)
                        
                        position = signal
                        entry_price = price
                        entry_symbol = symbol
                        print(f"✅ 开仓成功: {signal} {amount} @ ${price:.2}")
                    except Exception as e:
                        print(f"开仓失败: {e}")
                    
                    break
        
        time.sleep(15)
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    main()
