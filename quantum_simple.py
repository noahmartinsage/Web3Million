#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million 量子高频交易 - 简化版
直接运行，输出到日志文件
"""
import os
import sys
import json
import time
import random
from datetime import datetime

# 配置
INITIAL_BALANCE = 10.0  # 每智能体 10U
LEVERAGE = 50  # 50x 杠杆
SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
NUM_AGENTS = 5

# 模拟价格
prices = {
    'BTC': 95000.0,
    'ETH': 2500.0,
    'SOL': 180.0
}

class Agent:
    def __init__(self, aid, symbol):
        self.aid = aid
        self.symbol = symbol
        self.balance = INITIAL_BALANCE
        self.leverage = LEVERAGE
        self.position = None
        self.trades = 0
        self.wins = 0
        self.losses = 0
        self.pnl = 0.0
        self.scans = 0
        
    def run_step(self):
        self.scans += 1
        
        # 模拟价格波动
        base = prices[self.symbol.split('/')[0]]
        change = random.uniform(-0.002, 0.002)
        price = base * (1 + change)
        
        # 简单策略：RSI 模拟
        rsi = random.uniform(20, 80)
        
        if self.position is None:
            # 开仓信号
            if rsi < 30:
                self.position = {'side': 'LONG', 'entry': price}
                print(f"[A{self.aid}] BUY {self.symbol} @ {price:.2f}")
            elif rsi > 70:
                self.position = {'side': 'SHORT', 'entry': price}
                print(f"[A{self.aid}] SELL {self.symbol} @ {price:.2f}")
        else:
            # 平仓检查
            side = self.position['side']
            entry = self.position['entry']
            
            if side == 'LONG':
                pnl_pct = (price - entry) / entry
            else:
                pnl_pct = (entry - price) / entry
            
            # 止盈止损
            tp = 0.002  # 0.2% 价格变动 = 10% 账户收益 (50x)
            sl = -0.001  # -0.1% 价格变动 = -5% 账户损失
            
            if pnl_pct >= tp or pnl_pct <= sl:
                trade_pnl = self.balance * pnl_pct * self.leverage
                self.balance += trade_pnl
                self.pnl += trade_pnl
                self.trades += 1
                
                if trade_pnl > 0:
                    self.wins += 1
                    print(f"[A{self.aid}] WIN +${trade_pnl:.4f} | Bal: ${self.balance:.4f}")
                else:
                    self.losses += 1
                    print(f"[A{self.aid}] LOSS ${trade_pnl:.4f} | Bal: ${self.balance:.4f}")
                
                self.position = None
        
        return self.balance > 0

def main():
    print("=" * 60)
    print("Web3Million 量子高频交易系统 v1.0")
    print("=" * 60)
    print(f"启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"智能体数量：{NUM_AGENTS}")
    print(f"每智能体资金：${INITIAL_BALANCE}")
    print(f"杠杆：{LEVERAGE}x")
    print(f"交易对：{SYMBOLS}")
    print("=" * 60)
    
    # 创建智能体
    agents = []
    for i in range(NUM_AGENTS):
        symbol = SYMBOLS[i % len(SYMBOLS)]
        agents.append(Agent(i+1, symbol))
        print(f"智能体#{i+1} 创建：{symbol}")
    
    print("=" * 60)
    print("开始交易循环...\n")
    
    # 主循环
    start_time = datetime.now()
    report_interval = 30  # 30 秒汇报
    
    while True:
        for agent in agents:
            if not agent.run_step():
                print(f"[A{agent.aid}] 爆仓出局!")
                agents.remove(agent)
                break
        
        # 定期汇报
        elapsed = (datetime.now() - start_time).total_seconds()
        if elapsed > 0 and int(elapsed) % report_interval == 0:
            total_bal = sum(a.balance for a in agents)
            total_pnl = sum(a.pnl for a in agents)
            total_trades = sum(a.trades for a in agents)
            total_wins = sum(a.wins for a in agents)
            
            win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0
            
            print("\n" + "=" * 60)
            print(f"状态汇报 | 运行：{int(elapsed)}秒")
            print(f"总余额：${total_bal:.4f} (初始：${len(agents)*INITIAL_BALANCE:.2f})")
            print(f"总 PnL: ${total_pnl:+.4f}")
            print(f"交易数：{total_trades} | 胜率：{win_rate:.1f}%")
            print("=" * 60 + "\n")
        
        time.sleep(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n手动停止")
