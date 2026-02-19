#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million 高频量化交易系统 v4.0 - 升级版
- 多时间框架分析
- 智能止盈止损
- 资金管理优化
- 交易信号确认
"""
import ccxt
import pandas as pd
import numpy as np
import time
from datetime import datetime

class HFTraderV4:
    def __init__(self):
        self.exchange = ccxt.okx({
            'apiKey': 'b71ee824-5524-4cde-b818-b8e294c27d56',
            'secret': '76122A8879980469F474F042135584DB',
            'password': 'Qian159.',
            'testnet': True
        })
        
        self.symbol = 'ETH/USDT'
        self.initial_capital = 4776.38
        
        # 升级参数
        self.position_pct = 0.15      # 15%仓位
        self.stop_loss_pct = 0.01     # 1%止损
        self.take_profit_pct = 0.02   # 2%止盈
        
        # 状态
        self.position = None
        self.entry_price = 0
        self.trades = []
        self.daily_pnl = 0
        
    def get_balance(self):
        b = self.exchange.fetch_balance()
        return b['total'].get('USDT', 0), b['total'].get('ETH', 0)
    
    def get_price(self):
        return self.exchange.fetch_ticker(self.symbol)['last']
    
    def get_multi_tf_data(self):
        """多时间框架分析"""
        data = {}
        for tf, limit in [('1m', 60), ('5m', 50), ('15m', 30)]:
            ohlcv = self.exchange.fetch_ohlcv(self.symbol, tf, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['t','o','h','l','c','v'])
            data[tf] = df
        return data
    
    def calculate_indicators(self, df):
        """计算技术指标"""
        # RSI
        delta = df['c'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        df['rsi'] = 100 - (100 / (1 + gain / loss))
        
        # MACD
        ema12 = df['c'].ewm(span=12).mean()
        ema26 = df['c'].ewm(span=26).mean()
        df['macd'] = ema12 - ema26
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # MA
        df['ma5'] = df['c'].rolling(5).mean()
        df['ma20'] = df['c'].rolling(20).mean()
        
        # ATR
        high_low = df['h'] - df['l']
        high_close = abs(df['h'] - df['c'].shift())
        low_close = abs(df['l'] - df['c'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr'] = tr.rolling(14).mean()
        
        return df
    
    def get_signal(self, data):
        """多时间框架信号确认"""
        signals = {}
        
        for tf, df in data.items():
            df = self.calculate_indicators(df)
            latest = df.iloc[-1]
            
            # 短期趋势
            if latest['ma5'] > latest['ma20'] and latest['macd_hist'] > 0:
                signals[tf] = 'bullish'
            elif latest['ma5'] < latest['ma20'] and latest['macd_hist'] < 0:
                signals[tf] = 'bearish'
            else:
                signals[tf] = 'neutral'
        
        # 整体信号 (多周期确认)
        bullish_count = sum(1 for v in signals.values() if v == 'bullish')
        bearish_count = sum(1 for v in signals.values() if v == 'bearish')
        
        if bullish_count >= 2:
            return 'LONG'
        elif bearish_count >= 2:
            return 'SHORT'
        return 'NEUTRAL'
    
    def should_exit(self):
        """智能退出判断"""
        if not self.position:
            return False, None
        
        current = self.get_price()
        
        if self.position == 'LONG':
            pnl_pct = (current - self.entry_price) / self.entry_price
        else:
            pnl_pct = (self.entry_price - current) / self.entry_price
        
        # 止盈
        if pnl_pct >= self.take_profit_pct:
            return True, f'TP ({pnl_pct*100:+.1f}%)'
        # 止损
        if pnl_pct <= -self.stop_loss_pct:
            return True, f'SL ({pnl_pct*100:+.1f}%)'
        
        # 反向信号
        data = self.get_multi_tf_data()
        signal = self.get_signal(data)
        if signal == 'SHORT' and self.position == 'LONG':
            return True, f'REVERSE ({pnl_pct*100:+.1f}%)'
        if signal == 'LONG' and self.position == 'SHORT':
            return True, f'REVERSE ({pnl_pct*100:+.1f}%)'
        
        return False, None
    
    def open_position(self, side):
        """开仓"""
        usdt, eth = self.get_balance()
        if usdt < 10:
            return False
        
        amount = (usdt * self.position_pct) / self.get_price()
        amount = round(amount, 4)
        
        try:
            if side == 'LONG':
                self.exchange.create_market_buy_order(self.symbol, amount)
            else:
                self.exchange.create_market_sell_order(self.symbol, amount)
            
            self.position = side
            self.entry_price = self.get_price()
            
            print(f'[{datetime.now().strftime("%H:%M:%S")}] {side} OPEN: {amount} @ ${self.entry_price:.2}')
            return True
        except Exception as e:
            print(f'Open error: {e}')
            return False
    
    def close_position(self, reason):
        """平仓"""
        usdt, eth = self.get_balance()
        if eth < 0.001:
            self.position = None
            return
        
        try:
            if self.position == 'LONG':
                self.exchange.create_market_sell_order(self.symbol, eth)
            else:
                self.exchange.create_market_buy_order(self.symbol, eth)
            
            exit_price = self.get_price()
            pnl = (exit_price - self.entry_price) * eth if self.position == 'LONG' else (self.entry_price - exit_price) * eth
            
            print(f'[{datetime.now().strftime("%H:%M:%S")}] {self.position} CLOSE: {reason} @ ${exit_price:.2}, PnL: ${pnl:.2}')
            
            self.trades.append({'entry': self.entry_price, 'exit': exit_price, 'pnl': pnl, 'time': datetime.now()})
            self.position = None
            self.entry_price = 0
        except Exception as e:
            print(f'Close error: {e}')
    
    def run(self, iterations=100, interval=15):
        print('='*60)
        print('HF Trader V4.0 - Multi-Timeframe Analysis')
        print(f'Interval: {interval}s, Iterations: {iterations}')
        print('='*60)
        
        usdt, eth = self.get_balance()
        print(f'Initial: ${usdt:.2}')
        
        for i in range(iterations):
            try:
                # 检查平仓
                should_exit, reason = self.should_exit()
                if should_exit:
                    self.close_position(reason)
                
                # 获取信号
                data = self.get_multi_tf_data()
                signal = self.get_signal(data)
                
                # 开仓
                if not self.position and signal != 'NEUTRAL':
                    self.open_position(signal)
                
                # 状态
                usdt, eth = self.get_balance()
                price = self.get_price()
                total = usdt + eth * price
                pnl = total - self.initial_capital
                
                pos_info = ''
                if self.position:
                    current_pnl = (price - self.entry_price) / self.entry_price * 100 if self.position == 'LONG' else (self.entry_price - price) / self.entry_price * 100
                    pos_info = f' | {self.position} @ ${self.entry_price:.0} ({current_pnl:+.1f}%)'
                
                print(f'[{i+1}] {signal} | ${price:.0} | Total:${total:.0} | PnL:${pnl:.0}{pos_info}')
                
                time.sleep(interval)
                
            except Exception as e:
                print(f'Error: {e}')
                time.sleep(5)
        
        # Report
        usdt, eth = self.get_balance()
        total = usdt + eth * self.get_price()
        print('='*60)
        print(f'Final: ${total:.2} | PnL: ${total-self.initial_capital:.2} ({((total/self.initial_capital)-1)*100:.1f}%)')
        print(f'Trades: {len(self.trades)}')
        print('='*60)


if __name__ == '__main__':
    trader = HFTraderV4()
    trader.run(iterations=100, interval=12)
