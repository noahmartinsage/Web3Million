#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million 高频量化交易系统 v3.5
全自动交易，无需确认
"""
import ccxt
import pandas as pd
import numpy as np
import time
from datetime import datetime
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class HighFreqTrader:
    def __init__(self):
        self.exchange = ccxt.okx({
            'apiKey': 'b71ee824-5524-4cde-b818-b8e294c27d56',
            'secret': '76122A8879980469F474F042135584DB',
            'password': 'Qian159.',
            'testnet': True
        })
        
        self.symbol = 'ETH/USDT'
        self.initial_capital = 4776.38
        
        # 风控参数
        self.position_ratio = 0.1  # 10%仓位
        self.stop_loss = 0.015     # 1.5%止损
        self.take_profit = 0.03    # 3%止盈
        
        # 状态
        self.position = None  # LONG/SHORT/None
        self.entry_price = 0
        self.trades = []
        
    def get_balance(self):
        """获取余额"""
        balance = self.exchange.fetch_balance()
        usdt = balance['total'].get('USDT', 0)
        eth = balance['total'].get('ETH', 0)
        return usdt, eth
    
    def get_price(self):
        """获取当前价格"""
        return self.exchange.fetch_ticker(self.symbol)['last']
    
    def get_data(self, limit=50):
        """获取并计算指标"""
        ohlcv = self.exchange.fetch_ohlcv(self.symbol, '5m', limit=limit)
        df = pd.DataFrame(ohlcv, columns=['t', 'o', 'h', 'l', 'c', 'v'])
        
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
        
        return df
    
    def get_signal(self, df):
        """获取交易信号"""
        latest = df.iloc[-1]
        
        # 多指标确认
        rsi = latest['rsi']
        macd_hist = latest['macd_hist']
        ma_trend = latest['ma5'] > latest['ma20']
        
        # 买入信号: RSI超卖或MACD金叉+均线多头
        long_signal = (rsi < 35) or (macd_hist > 0 and ma_trend and rsi < 65)
        
        # 卖出信号: RSI超买或MACD死叉+均线空头
        short_signal = (rsi > 65) or (macd_hist < 0 and not ma_trend and rsi > 35)
        
        if long_signal and not short_signal:
            return 'LONG'
        elif short_signal and not long_signal:
            return 'SHORT'
        return 'NEUTRAL'
    
    def check_exit(self):
        """检查是否需要平仓"""
        if not self.position:
            return False, None
        
        current = self.get_price()
        
        if self.position == 'LONG':
            pnl_pct = (current - self.entry_price) / self.entry_price
        else:
            pnl_pct = (self.entry_price - current) / self.entry_price
        
        # 止盈
        if pnl_pct >= self.take_profit:
            return True, f'TP ({pnl_pct*100:.1f}%)'
        # 止损
        if pnl_pct <= -self.stop_loss:
            return True, f'SL ({pnl_pct*100:.1f}%)'
        
        # 反向信号
        df = self.get_data()
        signal = self.get_signal(df)
        if signal == 'SHORT' and self.position == 'LONG':
            return True, f'REVERSE ({pnl_pct*100:.1f}%)'
        if signal == 'LONG' and self.position == 'SHORT':
            return True, f'REVERSE ({pnl_pct*100:.1f}%)'
        
        return False, None
    
    def open_position(self, side):
        """开仓"""
        usdt, eth = self.get_balance()
        if usdt < 10:
            print('Insufficient USDT')
            return False
        
        amount = (usdt * self.position_ratio) / self.get_price()
        amount = round(amount, 4)
        
        try:
            if side == 'LONG':
                order = self.exchange.create_market_buy_order(self.symbol, amount)
            else:
                order = self.exchange.create_market_sell_order(self.symbol, amount)
            
            self.position = side
            self.entry_price = self.get_price()
            
            print(f'[{datetime.now().strftime("%H:%M:%S")}] {side} OPEN: {amount} ETH @ ${self.entry_price:.2}')
            return True
        except Exception as e:
            print(f'Open error: {e}')
            return False
    
    def close_position(self, reason):
        """平仓"""
        usdt, eth = self.get_balance()
        if eth < 0.001:
            self.position = None
            return False
        
        try:
            if self.position == 'LONG':
                order = self.exchange.create_market_sell_order(self.symbol, eth)
            else:
                order = self.exchange.create_market_buy_order(self.symbol, eth)
            
            exit_price = self.get_price()
            pnl = (exit_price - self.entry_price) * eth if self.position == 'LONG' else (self.entry_price - exit_price) * eth
            
            print(f'[{datetime.now().strftime("%H:%M:%S")}] {self.position} CLOSE: {reason} @ ${exit_price:.2}, PnL: ${pnl:.2}')
            
            self.trades.append({'entry': self.entry_price, 'exit': exit_price, 'pnl': pnl, 'time': datetime.now()})
            self.position = None
            self.entry_price = 0
            return True
        except Exception as e:
            print(f'Close error: {e}')
            return False
    
    def run(self, iterations=100, interval=15):
        """主循环"""
        print('='*60)
        print('🚀 高频量化交易系统 v3.5 启动')
        print(f'⏱️ 间隔: {interval}秒, 轮次: {iterations}')
        print('='*60)
        
        usdt, eth = self.get_balance()
        print(f'💰 初始: ${usdt:.2}')
        
        for i in range(iterations):
            try:
                # 检查平仓
                should_exit, reason = self.check_exit()
                if should_exit:
                    self.close_position(reason)
                
                # 获取信号
                df = self.get_data()
                signal = self.get_signal(df)
                
                # 开仓
                if not self.position and signal != 'NEUTRAL':
                    self.open_position(signal)
                
                # 状态输出
                usdt, eth = self.get_balance()
                total = usdt + eth * self.get_price()
                pnl = total - self.initial_capital
                
                status = f'{i+1}/{iterations} | {signal} | USDT:{usdt:.0} ETH:{eth:.3} Total:${total:.0} PnL:${pnl:.0}'
                if self.position:
                    current = self.get_price()
                    pnl_pct = (current - self.entry_price) / self.entry_price * 100 if self.position == 'LONG' else (self.entry_price - current) / self.entry_price * 100
                    status += f' | {self.position} @ ${self.entry_price:.0} ({pnl_pct:+.1f}%)'
                
                print(f'[{datetime.now().strftime("%H:%M:%S")}] {status}')
                
                time.sleep(interval)
                
            except Exception as e:
                print(f'Error: {e}')
                time.sleep(5)
        
        # 最终报告
        usdt, eth = self.get_balance()
        total = usdt + eth * self.get_price()
        print('='*60)
        print(f'📊 最终: ${total:.2} | 收益: ${total - self.initial_capital:.2} ({((total/self.initial_capital)-1)*100:.1f}%)')
        print(f'🔢 交易次数: {len(self.trades)}')
        print('='*60)


if __name__ == '__main__':
    trader = HighFreqTrader()
    trader.run(iterations=50, interval=10)  # 50轮, 每轮10秒
