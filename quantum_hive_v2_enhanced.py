#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million 量子蜂群 v2.0 - 增强版
功能特性:
- 多智能体协同交易
- 分批止盈策略 (3%/5%/8% 三档)
- 动态风险控制
- 7x24 小时稳定运行
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
    """量子智能体 - 支持分批止盈"""
    
    def __init__(self, agent_id: int, symbol: str, leverage: int = 50, initial_balance: float = 10.0):
        self.agent_id = agent_id
        self.symbol = symbol
        self.leverage = leverage
        self.balance = initial_balance
        self.initial_balance = initial_balance
        
        # 持仓管理
        self.position = None
        self.position_size = 0.0
        self.entry_price = 0.0
        
        # 统计
        self.trades = []
        self.scan_count = 0
        self.win_count = 0
        self.loss_count = 0
        self.total_pnl = 0.0
        
        # 运行状态
        self.running = True
        self.last_report = datetime.now()
        
        # 止盈止损配置 - 分批止盈
        self.stop_loss_pct = 0.05 / leverage  # 5% 账户风险止损
        self.take_profit_levels = [
            {'pct': 0.03 / leverage, 'sell_ratio': 0.5},   # 3% 收益卖出 50%
            {'pct': 0.05 / leverage, 'sell_ratio': 0.3},   # 5% 收益卖出 30%
            {'pct': 0.08 / leverage, 'sell_ratio': 0.2},   # 8% 收益卖出 20%
        ]
        
    def analyze_market(self, okx) -> Dict:
        """市场分析"""
        try:
            ohlcv = okx.fetch_ohlcv(self.symbol, '1m', limit=50)
            if not ohlcv or len(ohlcv) < 20:
                return {'signal': 'HOLD', 'rsi': 50}
            
            closes = [c[4] for c in ohlcv]
            rsi = self.calculate_rsi(closes, 7)
            
            # RSI 信号
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
        """计算 RSI"""
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
    
    def check_batch_take_profit(self, current_price: float) -> List[Dict]:
        """检查分批止盈条件，返回平仓操作列表"""
        if self.position is None or self.position_size <= 0:
            return []
        
        actions = []
        side = self.position['side']
        entry = self.position['entry_price']
        
        # 计算当前盈亏比
        if side == 'LONG':
            pnl_pct = (current_price - entry) / entry
        else:
            pnl_pct = (entry - current_price) / entry
        
        # 检查每个止盈档位
        remaining_ratio = 1.0
        for level in self.take_profit_levels:
            level_pnl_pct = level['pct']
            sell_ratio = level['sell_ratio']
            
            # 如果达到止盈条件
            if pnl_pct >= level_pnl_pct:
                # 计算卖出数量
                sell_ratio_of_remaining = sell_ratio * remaining_ratio
                if sell_ratio_of_remaining > 0:
                    actions.append({
                        'type': 'PARTIAL_CLOSE',
                        'ratio': sell_ratio_of_remaining,
                        'reason': f'止盈{level_pnl_pct*leverage*100:.0f}%',
                        'pnl_pct': pnl_pct
                    })
                    remaining_ratio -= sell_ratio_of_remaining
        
        # 检查止损
        if pnl_pct <= -self.stop_loss_pct * leverage:
            actions.append({
                'type': 'FULL_CLOSE',
                'reason': f'止损{-self.stop_loss_pct*100:.1f}%',
                'pnl_pct': pnl_pct
            })
        
        return actions
    
    def execute_trade(self, okx, signal: str, price: float):
        """执行交易 - 支持分批止盈"""
        if self.position is not None and self.position_size > 0:
            # 检查止盈止损
            actions = self.check_batch_take_profit(price)
            
            for action in actions:
                if action['type'] == 'PARTIAL_CLOSE':
                    # 部分平仓
                    close_ratio = action['ratio']
                    close_amount = self.position_size * close_ratio
                    pnl = close_amount * (price - self.entry_price) if self.position['side'] == 'LONG' else close_amount * (self.entry_price - price)
                    
                    self.balance += pnl
                    self.total_pnl += pnl
                    self.position_size -= close_amount
                    
                    result = 'WIN' if pnl > 0 else 'LOSS'
                    if pnl > 0:
                        self.win_count += 1
                    else:
                        self.loss_count += 1
                    
                    self.trades.append({
                        'type': 'PARTIAL_CLOSE',
                        'side': self.position['side'],
                        'entry': self.entry_price,
                        'exit': price,
                        'amount': close_amount,
                        'pnl': pnl,
                        'result': result,
                        'reason': action['reason'],
                        'time': datetime.now().isoformat()
                    })
                    
                    emoji = '✅' if pnl > 0 else '❌'
                    print(f"[Agent-{self.agent_id}] {emoji} 分批{action['reason']} | 平仓{close_amount:.4f} | PnL: ${pnl:.4f} | 余额：${self.balance:.4f}")
                    
                    # 如果仓位已平完
                    if self.position_size <= 0.001:
                        self.position = None
                        self.position_size = 0
                        break
                
                elif action['type'] == 'FULL_CLOSE':
                    # 全部平仓
                    close_amount = self.position_size
                    pnl = close_amount * (price - self.entry_price) if self.position['side'] == 'LONG' else close_amount * (self.entry_price - price)
                    
                    self.balance += pnl
                    self.total_pnl += pnl
                    
                    result = 'WIN' if pnl > 0 else 'LOSS'
                    if pnl > 0:
                        self.win_count += 1
                    else:
                        self.loss_count += 1
                    
                    self.trades.append({
                        'type': 'FULL_CLOSE',
                        'side': self.position['side'],
                        'entry': self.entry_price,
                        'exit': price,
                        'amount': close_amount,
                        'pnl': pnl,
                        'result': result,
                        'reason': action['reason'],
                        'time': datetime.now().isoformat()
                    })
                    
                    self.position = None
                    self.position_size = 0
                    
                    emoji = '✅' if pnl > 0 else '❌'
                    print(f"[Agent-{self.agent_id}] {emoji} {action['reason']} | 平仓{close_amount:.4f} | PnL: ${pnl:.4f} | 余额：${self.balance:.4f}")
                    break
        
        # 开新仓
        if self.position is None and signal in ['LONG', 'SHORT']:
            # 使用 50% 余额开仓
            position_value = self.balance * 0.5
            self.position_size = (position_value * self.leverage) / price
            self.entry_price = price
            self.position = {'side': signal, 'entry_price': price, 'entry_time': datetime.now().isoformat()}
            
            emoji = '🟢' if signal == 'LONG' else '🔴'
            print(f"[Agent-{self.agent_id}] {emoji} 开仓 {signal} @ ${price:.2f} ({self.leverage}x) | 数量：{self.position_size:.4f}")
    
    def run(self, okx):
        """运行智能体"""
        print(f"[Agent-{self.agent_id}] 🚀 启动 | {self.symbol} | {self.leverage}x | ${self.balance:.2f}")
        
        while self.running:
            try:
                data = self.analyze_market(okx)
                self.scan_count += 1
                
                if data.get('signal') and data.get('price'):
                    self.execute_trade(okx, data['signal'], data['price'])
                
                # 定期报告
                if (datetime.now() - self.last_report).total_seconds() > 30:
                    print(f"[Agent-{self.agent_id}] 扫描：{self.scan_count} | PnL: ${self.total_pnl:.4f} | 余额：${self.balance:.4f}")
                    self.last_report = datetime.now()
                
                time.sleep(random.uniform(3, 5))
            except Exception as e:
                print(f"[Agent-{self.agent_id}] 错误：{e}")
                time.sleep(5)
    
    def stop(self):
        """停止智能体"""
        self.running = False


class QuantumHive:
    """量子蜂巢 - 多智能体管理系统"""
    
    def __init__(self, initial_capital_per_agent: float = 10.0, max_agents: int = 10, leverage_range: tuple = (25, 50)):
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
                'options': {'defaultType': 'swap'}
            })
            self.okx.set_sandbox_mode(True)
            self.okx.session.trust_env = False
            self.okx.session.proxies = {}
            print("✅ OKX 测试网连接成功")
        except Exception as e:
            print(f"❌ OKX 连接失败：{e}")
            raise
        
        # 初始化智能体
        self._init_agents()
    
    def _init_agents(self):
        """初始化智能体"""
        symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT']
        
        for i in range(min(self.max_agents, len(symbols) * 2)):
            symbol = symbols[i % len(symbols)]
            leverage = random.randint(self.leverage_range[0], self.leverage_range[1])
            agent = QuantumAgent(i, symbol, leverage, self.initial_capital_per_agent)
            self.agents.append(agent)
            self.total_capital += self.initial_capital_per_agent
            print(f"🐝 智能体 {i} 已创建 | {symbol} | {leverage}x | ${self.initial_capital_per_agent:.2f}")
    
    def run(self):
        """运行蜂巢"""
        print("\n" + "="*80)
        print("🐝 Web3Million 量子蜂巢 v2.0 - 启动")
        print(f"启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"智能体数量：{len(self.agents)}")
        print(f"总资本：${self.total_capital:.2f}")
        print("="*80 + "\n")
        
        # 启动所有智能体
        threads = []
        for agent in self.agents:
            thread = threading.Thread(target=agent.run, args=(self.okx,))
            thread.daemon = True
            threads.append(thread)
            thread.start()
        
        # 主循环
        try:
            while self.running:
                time.sleep(10)
                
                # 定期总览
                total_pnl = sum(a.total_pnl for a in self.agents)
                total_balance = sum(a.balance for a in self.agents)
                total_scans = sum(a.scan_count for a in self.agents)
                total_wins = sum(a.win_count for a in self.agents)
                total_losses = sum(a.loss_count for a in self.agents)
                
                print("\n" + "="*80)
                print(f"📊 蜂巢总览 | 扫描：{total_scans} | 盈利：{total_wins} | 亏损：{total_losses} | 总 PnL: ${total_pnl:.4f} | 总余额：${total_balance:.4f}")
                print("="*80 + "\n")
        except KeyboardInterrupt:
            print("\n🛑 收到停止信号，关闭蜂巢...")
            self.stop()
    
    def stop(self):
        """停止蜂巢"""
        self.running = False
        for agent in self.agents:
            agent.stop()
        print("🐝 量子蜂巢已停止")


if __name__ == '__main__':
    try:
        hive = QuantumHive(
            initial_capital_per_agent=10.0,
            max_agents=6,
            leverage_range=(25, 50)
        )
        hive.run()
    except Exception as e:
        print(f"❌ 量子蜂巢异常：{e}")
        import traceback
        traceback.print_exc()
