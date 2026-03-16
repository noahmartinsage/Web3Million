#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million 量子蜂群启动器 - Windows 修复版
解决输出编码问题，确保 7x24 小时稳定运行
"""
import sys
import io

# 强制 UTF-8 输出
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import os
import json
import time
import random
import threading
from datetime import datetime
from typing import Dict, List, Optional
import ccxt

# 清除代理
for var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    os.environ.pop(var, None)

class QuantumAgent:
    def __init__(self, agent_id: int, symbol: str, leverage: int = 50, 
                 initial_balance: float = 10.0):
        self.agent_id = agent_id
        self.symbol = symbol
        self.leverage = leverage
        self.balance = initial_balance
        self.initial_balance = initial_balance
        self.position = None
        self.trades = []
        self.scan_count = 0
        self.win_count = 0
        self.loss_count = 0
        self.total_pnl = 0.0
        self.running = True
        self.last_report = datetime.now()
        
        # 止盈止损
        self.stop_loss_pct = 0.03 / leverage
        self.take_profit_pct = 0.10 / leverage
        
    def analyze_market(self, okx) -> Dict:
        try:
            ohlcv = okx.fetch_ohlcv(self.symbol, '1m', limit=50)
            if not ohlcv or len(ohlcv) < 20:
                return {'signal': 'HOLD', 'rsi': 50}
            
            closes = [c[4] for c in ohlcv]
            rsi = self.calculate_rsi(closes, 7)
            
            # 简单信号
            if rsi < 35:
                signal = 'LONG'
            elif rsi > 65:
                signal = 'SHORT'
            else:
                signal = 'HOLD'
            
            return {'signal': signal, 'rsi': rsi, 'price': closes[-1]}
        except Exception as e:
            return {'signal': 'HOLD', 'rsi': 50, 'error': str(e)}
    
    def calculate_rsi(self, prices: List[float], period: int = 7) -> float:
        if len(prices) < period + 1:
            return 50.0
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas[-period:]]
        losses = [-d if d < 0 else 0 for d in deltas[-period:]]
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        if avg_loss == 0:
            return 100.0
        return 100.0 - (100.0 / (1.0 + avg_gain / avg_loss))
    
    def execute_trade(self, okx, signal: str, price: float):
        if self.position is not None:
            side = self.position['side']
            entry = self.position['entry_price']
            pnl_pct = (price - entry) / entry if side == 'LONG' else (entry - price) / entry
            
            if pnl_pct >= self.take_profit_pct or pnl_pct <= -self.stop_loss_pct:
                pnl = self.balance * pnl_pct * self.leverage
                self.balance += pnl
                self.total_pnl += pnl
                result = 'WIN' if pnl > 0 else 'LOSS'
                if pnl > 0:
                    self.win_count += 1
                else:
                    self.loss_count += 1
                
                self.trades.append({
                    'side': side, 'entry': entry, 'exit': price,
                    'pnl': pnl, 'result': result, 'time': datetime.now().isoformat()
                })
                
                emoji = '✅' if pnl > 0 else '❌'
                print(f"[Agent-{self.agent_id}] {emoji} 平仓 {side} | PnL: ${pnl:.4f} | 余额：${self.balance:.4f}")
                self.position = None
        else:
            if signal in ['LONG', 'SHORT']:
                self.position = {'side': signal, 'entry_price': price, 'entry_time': datetime.now().isoformat()}
                emoji = '🟢' if signal == 'LONG' else '🔴'
                print(f"[Agent-{self.agent_id}] {emoji} 开仓 {signal} @ ${price:.2f} ({self.leverage}x)")
    
    def run(self, okx):
        print(f"[Agent-{self.agent_id}] 🚀 启动 | {self.symbol} | {self.leverage}x | ${self.balance:.2f}")
        while self.running:
            try:
                data = self.analyze_market(okx)
                self.scan_count += 1
                
                if data.get('signal') and data.get('price'):
                    self.execute_trade(okx, data['signal'], data['price'])
                
                if (datetime.now() - self.last_report).total_seconds() > 30:
                    print(f"[Agent-{self.agent_id}] 扫描：{self.scan_count} | PnL: ${self.total_pnl:.4f} | 余额：${self.balance:.4f}")
                    self.last_report = datetime.now()
                
                time.sleep(random.uniform(3, 5))
            except Exception as e:
                print(f"[Agent-{self.agent_id}] 错误：{e}")
                time.sleep(5)
    
    def stop(self):
        self.running = False


class QuantumHive:
    def __init__(self, initial_capital_per_agent: float = 10.0, max_agents: int = 10, 
                 leverage_range: tuple = (25, 50)):
        self.initial_capital_per_agent = initial_capital_per_agent
        self.max_agents = max_agents
        self.leverage_range = leverage_range
        self.agents: List[QuantumAgent] = []
        self.total_capital = 0.0
        self.start_time = datetime.now()
        self.running = True
        self.okx = None
        
        # 连接 OKX
        try:
            with open('okx_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self.okx = ccxt.okx({
                'apiKey': config['api_key'],
                'secret': config['secret_key'],
                'password': config['passphrase'],
                'enableRateLimit': True,
                'options': {'defaultType': 'swap'},
                'timeout': 30000,
            })
            self.okx.set_sandbox_mode(True)
            self.okx.session.trust_env = False
            self.okx.session.proxies = {}
            print("✅ OKX 测试网连接成功")
        except Exception as e:
            print(f"⚠️ OKX 初始化失败：{e}")
            self.okx = None
        
        self.symbol_pool = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT']
    
    def spawn_agent(self, symbol: str = None) -> QuantumAgent:
        if len(self.agents) >= self.max_agents:
            return None
        
        symbol = symbol or random.choice(self.symbol_pool)
        leverage = random.randint(self.leverage_range[0], self.leverage_range[1])
        agent_id = len(self.agents) + 1
        
        agent = QuantumAgent(
            agent_id=agent_id, symbol=symbol, leverage=leverage,
            initial_balance=self.initial_capital_per_agent
        )
        self.agents.append(agent)
        self.total_capital += self.initial_capital_per_agent
        
        print(f"🆕 智能体#{agent_id} | {symbol} | {leverage}x | ${self.initial_capital_per_agent:.2f}")
        return agent
    
    def hive_status(self):
        total_balance = sum(a.balance for a in self.agents)
        total_pnl = sum(a.total_pnl for a in self.agents)
        total_trades = sum(len(a.trades) for a in self.agents)
        total_wins = sum(a.win_count for a in self.agents)
        total_losses = sum(a.loss_count for a in self.agents)
        win_rate = (total_wins / (total_wins + total_losses) * 100) if (total_wins + total_losses) > 0 else 0
        roi = ((total_balance - self.total_capital) / self.total_capital) * 100
        runtime = datetime.now() - self.start_time
        
        print("\n" + "="*70)
        print(f"🐝 量子蜂巢状态 | 运行：{runtime}")
        print(f"智能体：{len(self.agents)}/{self.max_agents} | 活跃：{sum(1 for a in self.agents if a.running)}")
        print(f"总资金：${total_balance:.4f} (初始：${self.total_capital:.4f}) | ROI: {roi:+.2f}%")
        print(f"总交易：{total_trades} | 胜率：{win_rate:.1f}% | PnL: ${total_pnl:.4f}")
        print("="*70 + "\n")
    
    def run(self):
        print("\n" + "="*70)
        print("🚀 Web3Million 量子蜂群 v1.0 - Windows 修复版")
        print(f"启动：{self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"配置：${self.initial_capital_per_agent}/智能体 | {self.leverage_range[0]}-{self.leverage_range[1]}x | 最大{self.max_agents}个")
        print("="*70 + "\n")
        
        # 创建初始 5 个智能体
        print("🐝 创建初始智能体群...")
        for i in range(5):
            self.spawn_agent()
            time.sleep(0.5)
        
        # 启动线程
        threads = []
        for agent in self.agents:
            t = threading.Thread(target=agent.run, args=(self.okx,), daemon=True)
            t.start()
            threads.append(t)
            time.sleep(1)
        
        print("\n✅ 所有智能体已启动，开始交易...\n")
        
        # 主循环
        last_report = datetime.now()
        while self.running:
            time.sleep(1)
            if (datetime.now() - last_report).total_seconds() > 60:
                self.hive_status()
                last_report = datetime.now()
    
    def stop(self):
        print("\n🛑 停止所有智能体...")
        self.running = False
        for agent in self.agents:
            agent.stop()


if __name__ == '__main__':
    try:
        hive = QuantumHive(initial_capital_per_agent=10.0, max_agents=10, leverage_range=(25, 50))
        hive.run()
    except KeyboardInterrupt:
        print("\n\n👋 手动停止")
        if 'hive' in dir():
            hive.stop()
    except Exception as e:
        print(f"\n❌ 错误：{e}")
        import traceback
        traceback.print_exc()
