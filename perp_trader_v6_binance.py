#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million Perpetual v6 - Binance Version
Market data from Binance (more reliable in current network)
"""
import ccxt
import pandas as pd
import time
import sys
import os
import json
from datetime import datetime

sys.stdout = sys.__stdout__
sys.stderr = sys.__stderr__

class PerpetualTraderV6Binance:
    def __init__(self):
        # Use Binance for market data (more reliable)
        self.exchange = ccxt.binanceusdm({
            'enableRateLimit': True
        })
        
        self.symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT']
        
        # Risk Management
        self.position_pct = 0.02
        self.max_position_usdt = 50
        self.leverage = 30
        self.stop_loss_pct = 0.02
        self.take_profit_pct = 0.06
        self.cooldown_seconds = 300
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        
        self.position = None
        self.symbol = None
        self.entry_price = 0
        self.trades = []
        self.total_pnl = 0
        
        print("=" * 60)
        print("Web3Million Perpetual v6 - Binance Edition")
        print("=" * 60)
        print("Loading markets...")
        self.exchange.load_markets()
        print("Markets loaded!")
    
    def fetch_ohlcv(self, symbol, timeframe='1h', limit=100):
        """Fetch OHLCV data"""
        return self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    
    def calculate_rsi(self, prices, period=14):
        """Calculate RSI"""
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def check_signals(self, symbol):
        """Check trading signals"""
        try:
            ohlcv = self.fetch_ohlcv(symbol, timeframe='1h', limit=100)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            close_prices = df['close'].tolist()
            current_price = close_prices[-1]
            
            rsi = self.calculate_rsi(close_prices)
            
            # Simple MA
            ma5 = sum(close_prices[-5:]) / 5
            ma20 = sum(close_prices[-20:]) / 20
            
            print(f"\n{symbol}")
            print(f"  Price: ${current_price:,.2f}")
            print(f"  RSI: {rsi:.2f}")
            print(f"  MA5: ${ma5:,.2f} | MA20: ${ma20:,.2f}")
            
            # Signals
            long_signal = rsi < self.rsi_oversold and ma5 > ma20
            short_signal = rsi > self.rsi_overbought and ma5 < ma20
            
            if long_signal:
                print(f"  Signal: LONG (RSI oversold + MA bullish)")
                return 'LONG'
            elif short_signal:
                print(f"  Signal: SHORT (RSI overbought + MA bearish)")
                return 'SHORT'
            else:
                print(f"  Signal: HOLD")
                return 'HOLD'
                
        except Exception as e:
            print(f"Error analyzing {symbol}: {e}")
            return 'ERROR'
    
    def run_scan(self):
        """Scan all symbols"""
        print(f"\n{'='*60}")
        print(f"[SCAN] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        results = {}
        for symbol in self.symbols:
            results[symbol] = self.check_signals(symbol)
            time.sleep(0.5)  # Rate limit
        
        return results

if __name__ == '__main__':
    trader = PerpetualTraderV6Binance()
    
    print("\nStarting market scan...")
    results = trader.run_scan()
    
    print(f"\n{'='*60}")
    print("[SUMMARY]")
    for symbol, signal in results.items():
        print(f"  {symbol}: {signal}")
    print(f"{'='*60}")
