#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million Perpetual v6 - 7x24 模拟交易 (自动重启版)
"""
import random
import time
import json
from datetime import datetime
import sys

class PerpetualTraderV6Sim:
    def __init__(self):
        self.balance = 1288.38
        self.initial_balance = 1288.38
        self.prices = {
            'BTC/USDT:USDT': 95000,
            'ETH/USDT:USDT': 2000,
            'SOL/USDT:USDT': 100
        }
        self.position_pct = 0.02
        self.leverage = 30
        self.stop_loss_pct = 0.02
        self.take_profit_pct = 0.06
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        self.position = None
        self.trades = []
        self.scan_count = 0
        self.session_start = datetime.now()
        
    def simulate_price_movement(self):
        for symbol in self.prices:
            change = random.uniform(-0.002, 0.002)
            self.prices[symbol] *= (1 + change)
    
    def calculate_rsi(self, symbol):
        return random.uniform(25, 75)
    
    def check_signal(self, symbol):
        rsi = self.calculate_rsi(symbol)
        if rsi <= self.rsi_oversold:
            return 'LONG'
        elif rsi >= self.rsi_overbought:
            return 'SHORT'
        return 'HOLD'
    
    def run(self):
        try:
            while True:
                self.scan_count += 1
                self.simulate_price_movement()
                
                for symbol in self.prices:
                    signal = self.check_signal(symbol)
                    
                    if signal != 'HOLD' and self.position is None:
                        self.position = {
                            'symbol': symbol,
                            'side': signal,
                            'entry_price': self.prices[symbol],
                            'size': self.balance * self.position_pct / self.prices[symbol] * self.leverage,
                            'time': datetime.now().isoformat()
                        }
                        print(f"[{self.scan_count}] OPEN {signal} {symbol} @ ${self.prices[symbol]:.2f}", flush=True)
                        self.trades.append(self.position.copy())
                    elif self.position:
                        pnl_pct = (self.prices[self.position['symbol']] - self.position['entry_price']) / self.position['entry_price']
                        if self.position['side'] == 'SHORT':
                            pnl_pct = -pnl_pct
                        
                        if pnl_pct >= self.take_profit_pct or pnl_pct <= -self.stop_loss_pct:
                            pnl = self.position['size'] * self.position['entry_price'] * pnl_pct / self.leverage
                            self.balance += pnl
                            side = '[+]' if pnl > 0 else '[-]'
                            print(f"[{self.scan_count}] {side} CLOSE {self.position['side']} {self.position['symbol']} | PnL: ${pnl:.2f} | Balance: ${self.balance:.2f}", flush=True)
                            self.position = None
                
                # 每 60 次扫描输出状态
                if self.scan_count % 60 == 0:
                    runtime = (datetime.now() - self.session_start).total_seconds() / 60
                    print(f"\n{'='*50}", flush=True)
                    print(f"Runtime: {runtime:.1f} min", flush=True)
                    print(f"Scans: {self.scan_count}", flush=True)
                    print(f"Balance: ${self.balance:.2f}", flush=True)
                    print(f"PnL: ${self.balance - self.initial_balance:.2f} ({(self.balance/self.initial_balance-1)*100:.2f}%)", flush=True)
                    print(f"Trades: {len(self.trades)}", flush=True)
                    if self.position:
                        print(f"Position: {self.position['side']} {self.position['symbol']}", flush=True)
                    else:
                        print(f"Status: Waiting", flush=True)
                    print(f"{'='*50}\n", flush=True)
                
                # 常规输出
                if self.position:
                    pnl_pct = (self.prices[self.position['symbol']] - self.position['entry_price']) / self.position['entry_price']
                    if self.position['side'] == 'SHORT':
                        pnl_pct = -pnl_pct
                    print(f"[{self.scan_count}] HOLD {self.position['side']} {self.position['symbol']} | PnL: {pnl_pct*100:.2f}% | Balance: ${self.balance:.2f}", flush=True)
                else:
                    print(f"[{self.scan_count}] Idle | Balance: ${self.balance:.2f}", flush=True)
                
                time.sleep(30)
                
        except KeyboardInterrupt:
            self.print_summary()
            sys.exit(0)
    
    def print_summary(self):
        runtime = (datetime.now() - self.session_start).total_seconds() / 60
        print(f"\n{'='*50}", flush=True)
        print("STOPPED", flush=True)
        print(f"Runtime: {runtime:.1f} min", flush=True)
        print(f"Total Scans: {self.scan_count}", flush=True)
        print(f"Final Balance: ${self.balance:.2f}", flush=True)
        print(f"Total PnL: ${self.balance - self.initial_balance:.2f} ({(self.balance/self.initial_balance-1)*100:.2f}%)", flush=True)
        print(f"Total Trades: {len(self.trades)}", flush=True)
        print(f"{'='*50}", flush=True)

def main():
    session_num = 1
    while True:
        print(f"\n{'='*60}", flush=True)
        print(f"Web3Million Perpetual v6 - 7x24 Simulation", flush=True)
        print(f"Session #{session_num} | Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
        print(f"{'='*60}\n", flush=True)
        
        trader = PerpetualTraderV6Sim()
        try:
            trader.run()
        except Exception as e:
            print(f"\nSession Error: {e}", flush=True)
            print(f"Restarting in 10 seconds...", flush=True)
            time.sleep(10)
            session_num += 1

if __name__ == '__main__':
    main()
