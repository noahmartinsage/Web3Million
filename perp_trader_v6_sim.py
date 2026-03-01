#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million Perpetual v6 - 模拟模式 (无网络依赖)
用于演示和网络受限环境
"""
import random
import time
import json
from datetime import datetime

class PerpetualTraderV6Sim:
    def __init__(self):
        # 模拟初始资金
        self.balance = 1288.38
        self.initial_balance = 1288.38
        
        # 模拟价格
        self.prices = {
            'BTC/USDT:USDT': 95000,
            'ETH/USDT:USDT': 2000,
            'SOL/USDT:USDT': 100
        }
        
        # 参数
        self.position_pct = 0.02
        self.leverage = 30
        self.stop_loss_pct = 0.02
        self.take_profit_pct = 0.06
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        
        self.position = None
        self.trades = []
        self.scan_count = 0
        
        print("=" * 60)
        print("Web3Million Perpetual v6 - 模拟模式")
        print("=" * 60)
        print(f"初始资金：${self.initial_balance}")
        print("扫描间隔：30 秒")
        print("按 Ctrl+C 停止")
        print("=" * 60)
    
    def simulate_price_movement(self):
        """模拟价格波动"""
        for symbol in self.prices:
            change = random.uniform(-0.002, 0.002)
            self.prices[symbol] *= (1 + change)
    
    def calculate_rsi(self, symbol):
        """模拟 RSI"""
        return random.uniform(25, 75)
    
    def check_signal(self, symbol):
        """检查交易信号"""
        rsi = self.calculate_rsi(symbol)
        
        if rsi <= self.rsi_oversold:
            return 'LONG'
        elif rsi >= self.rsi_overbought:
            return 'SHORT'
        return 'HOLD'
    
    def run(self):
        """主循环"""
        try:
            while True:
                self.scan_count += 1
                self.simulate_price_movement()
                
                # 检查信号
                for symbol in self.prices:
                    signal = self.check_signal(symbol)
                    
                    if signal != 'HOLD' and self.position is None:
                        # 模拟开仓
                        self.position = {
                            'symbol': symbol,
                            'side': signal,
                            'entry_price': self.prices[symbol],
                            'size': self.balance * self.position_pct / self.prices[symbol] * self.leverage,
                            'time': datetime.now().isoformat()
                        }
                        print(f"[{self.scan_count}] OPEN {signal} {symbol} @ ${self.prices[symbol]:.2f}")
                        self.trades.append(self.position.copy())
                    elif self.position:
                        # 检查平仓
                        pnl_pct = (self.prices[self.position['symbol']] - self.position['entry_price']) / self.position['entry_price']
                        if self.position['side'] == 'SHORT':
                            pnl_pct = -pnl_pct
                        
                        if pnl_pct >= self.take_profit_pct or pnl_pct <= -self.stop_loss_pct:
                            pnl = self.position['size'] * self.position['entry_price'] * pnl_pct / self.leverage
                            self.balance += pnl
                            print(f"[{self.scan_count}] CLOSE {self.position['side']} {self.position['symbol']} | PnL: ${pnl:.2f} | Balance: ${self.balance:.2f}")
                            self.position = None
                
                # 状态输出
                if self.position:
                    pnl_pct = (self.prices[self.position['symbol']] - self.position['entry_price']) / self.position['entry_price']
                    if self.position['side'] == 'SHORT':
                        pnl_pct = -pnl_pct
                    print(f"[{self.scan_count}] HOLD {self.position['side']} {self.position['symbol']} | PnL: {pnl_pct*100:.2f}% | Balance: ${self.balance:.2f}")
                else:
                    print(f"[{self.scan_count}] Idle | Balance: ${self.balance:.2f}")
                
                time.sleep(30)
                
        except KeyboardInterrupt:
            print(f"\n停止交易 | 总扫描：{self.scan_count} | 最终资金：${self.balance:.2f}")
            print(f"总盈亏：${self.balance - self.initial_balance:.2f} ({(self.balance/self.initial_balance-1)*100:.2f}%)")

if __name__ == '__main__':
    trader = PerpetualTraderV6Sim()
    trader.run()
