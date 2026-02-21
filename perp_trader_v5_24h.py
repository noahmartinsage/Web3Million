#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million Perpetual v5 - Robust 24/7 Trading System
"""
import ccxt
import pandas as pd
import time
import sys
from datetime import datetime

# Force unbuffered output
sys.stdout = sys.__stdout__
sys.stderr = sys.__stderr__

class PerpetualTraderV5:
    def __init__(self):
        self.exchange = ccxt.okx({
            'apiKey': 'b71ee824-5524-4cde-b818-b8e294c27d56',
            'secret': '76122A8879980469F474F042135584DB',
            'password': 'Qian159.',
            'testnet': True,
            'options': {'defaultType': 'swap'},
            'enableRateLimit': True
        })
        
        self.symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT']
        
        # Params
        self.max_position_usdt = 20
        self.min_position_eth = 0.01
        self.leverage = 50
        self.stop_loss_pct = 0.015
        self.take_profit_pct = 0.10
        
        # State
        self.position = None
        self.symbol = None
        self.entry_price = 0
        self.trades = []
        self.total_pnl = 0
        
        print("="*60)
        print("Web3Million Perpetual v5 - 24/7 Mode")
        print("="*60)
        
        print("Loading markets...")
        self.exchange.load_markets()
        print("Markets loaded!")
    
    def get_balance(self):
        try:
            bal = self.exchange.fetch_balance()
            return bal['total'].get('USDT', 0)
        except:
            return 0
    
    def get_ticker(self, symbol):
        try:
            return self.exchange.fetch_ticker(symbol)
        except:
            return None
    
    def set_leverage(self, symbol, leverage):
        try:
            self.exchange.set_leverage(leverage, symbol)
            return True
        except:
            return False
    
    def calculate_indicators(self, df):
        if df.empty or len(df) < 30:
            return df
        
        closes = df['c']
        
        # RSI
        delta = closes.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        df['rsi'] = 100 - (100 / (1 + gain / loss))
        
        # MACD
        ema12 = closes.ewm(span=12).mean()
        ema26 = closes.ewm(span=26).mean()
        df['macd'] = ema12 - ema26
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # MA
        df['ma5'] = closes.rolling(5).mean()
        df['ma20'] = closes.rolling(20).mean()
        
        return df
    
    def get_signal(self, symbol):
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, '15m', limit=50)
            df = pd.DataFrame(ohlcv, columns=['t','o','h','l','c','v'])
            df = self.calculate_indicators(df)
            
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            
            rsi = latest['rsi']
            macd_hist = latest['macd_hist']
            macd_hist_prev = prev['macd_hist']
            ma_trend = 1 if latest['ma5'] > latest['ma20'] else -1
            
            if rsi <= 35 and macd_hist > macd_hist_prev and ma_trend > 0:
                return 'LONG', latest['c'], rsi
            elif rsi >= 65 and macd_hist < macd_hist_prev and ma_trend < 0:
                return 'SHORT', latest['c'], rsi
            
            return 'NEUTRAL', latest['c'], rsi
        except Exception as e:
            print(f"Signal error {symbol}: {e}")
            return 'NEUTRAL', 0, 50
    
    def scan_opportunities(self):
        for symbol in self.symbols:
            signal, price, rsi = self.get_signal(symbol)
            if signal != 'NEUTRAL':
                return {'symbol': symbol, 'signal': signal, 'price': price, 'rsi': rsi}
        return None
    
    def open_position(self, symbol, side, amount):
        try:
            self.set_leverage(symbol, self.leverage)
            
            if side == 'LONG':
                order = self.exchange.create_market_buy_order(symbol, amount)
            else:
                order = self.exchange.create_market_sell_order(symbol, amount)
            
            self.symbol = symbol
            self.position = side
            self.entry_price = self.get_ticker(symbol)['last']
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [OPEN] {side} {symbol} {amount} @ ${self.entry_price}")
            return True
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Open error: {e}")
            return False
    
    def close_position(self, reason):
        if not self.position or not self.symbol:
            return
        
        try:
            positions = self.exchange.fetch_positions([self.symbol])
            pos_size = 0
            for p in positions:
                if p.get('size', 0) != 0:
                    pos_size = abs(float(p.get('size', 0)))
                    break
            
            if pos_size > 0:
                if self.position == 'LONG':
                    self.exchange.create_market_sell_order(self.symbol, pos_size)
                else:
                    self.exchange.create_market_buy_order(self.symbol, pos_size)
                
                current = self.get_ticker(self.symbol)['last']
                
                if self.position == 'LONG':
                    pnl = (current - self.entry_price) * pos_size
                else:
                    pnl = (self.entry_price - current) * pos_size
                
                self.total_pnl += pnl
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [CLOSE] {self.position} {reason} @ ${current}, PnL: ${pnl:.2}")
                
                self.trades.append({
                    'symbol': self.symbol,
                    'side': self.position,
                    'entry': self.entry_price,
                    'exit': current,
                    'pnl': pnl,
                    'time': datetime.now().isoformat()
                })
            
            self.position = None
            self.symbol = None
            self.entry_price = 0
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Close error: {e}")
    
    def check_exit(self):
        if not self.position or not self.symbol:
            return False, None
        
        current = self.get_ticker(self.symbol)['last']
        
        if self.position == 'LONG':
            pnl_pct = (current - self.entry_price) / self.entry_price
        else:
            pnl_pct = (self.entry_price - current) / self.entry_price
        
        if pnl_pct <= -self.stop_loss_pct:
            return True, f"SL {pnl_pct*100:.1f}%"
        
        if pnl_pct >= self.take_profit_pct:
            return True, f"TP {pnl_pct*100:.1f}%"
        
        return False, None
    
    def run_forever(self, interval=30):
        print(f"\nStarting 24/7 trading... (interval: {interval}s)")
        print("Press Ctrl+C to stop\n")
        
        i = 0
        while True:
            try:
                i += 1
                usdt = self.get_balance()
                
                # Check exit
                if self.position:
                    should_exit, reason = self.check_exit()
                    if should_exit:
                        self.close_position(reason)
                
                # Open new position
                if not self.position:
                    opp = self.scan_opportunities()
                    if opp:
                        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] [Signal] {opp['signal']} {opp['symbol']} @ ${opp['price']} RSI:{opp['rsi']:.1f}")
                        amount = self.min_position_eth
                        self.open_position(opp['symbol'], opp['signal'], amount)
                
                # Status
                status = f"[{i}] "
                if self.position:
                    current = self.get_ticker(self.symbol)['last']
                    if self.position == 'LONG':
                        pnl_pct = (current - self.entry_price) / self.entry_price * 100
                    else:
                        pnl_pct = (self.entry_price - current) / self.entry_price * 100
                    status += f"Holding: {self.position} {self.symbol.split('/')[0]} @ ${current:.0} ({pnl_pct:+.1f}%)"
                else:
                    status += f"Idle | USDT: ${usdt:.2}"
                
                print(status)
                time.sleep(interval)
                
            except KeyboardInterrupt:
                print("\n\nStopping...")
                break
            except Exception as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Error: {e}")
                time.sleep(10)
        
        self.print_report()
    
    def print_report(self):
        print("\n" + "="*60)
        print("FINAL REPORT")
        print("="*60)
        print(f"Total PnL: ${self.total_pnl:.2}")
        print(f"Total Trades: {len(self.trades)}")
        print("="*60)


if __name__ == "__main__":
    trader = PerpetualTraderV5()
    trader.run_forever(interval=30)
