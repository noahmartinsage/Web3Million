#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million 量子高频交易智能体系统 v1.0
- 10U 起步，高倍杠杆 (25x-50x)
- 量子级策略：0.05%-0.1% 触发频率
- 7*24 小时自动交易
- 无限分身扩展能力
- 实时性能监控和汇报
"""
import os
import sys
# 强制 UTF-8 输出编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import json
import time
import random
import threading
from datetime import datetime
from typing import Dict, List, Optional
import ccxt

# 清除代理设置
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)

class QuantumAgent:
    """单个量子交易智能体"""
    
    def __init__(self, agent_id: int, symbol: str, leverage: int = 50, 
                 initial_balance: float = 10.0, trigger_threshold: float = 0.001):
        self.agent_id = agent_id
        self.symbol = symbol
        self.leverage = leverage  # 25x-50x
        self.balance = initial_balance
        self.initial_balance = initial_balance
        self.trigger_threshold = trigger_threshold  # 0.05%-0.1%
        self.position = None
        self.trades = []
        self.scan_count = 0
        self.win_count = 0
        self.loss_count = 0
        self.total_pnl = 0.0
        self.running = True
        self.last_report = datetime.now()
        
        # 止盈止损 (账户风险)
        self.stop_loss_pct = 0.03 / leverage  # 3% 账户风险
        self.take_profit_pct = 0.10 / leverage  # 10% 账户收益
        
    def fetch_price(self, okx) -> Optional[float]:
        """获取最新价格"""
        try:
            ticker = okx.fetch_ticker(self.symbol)
            return ticker['last']
        except Exception as e:
            print(f"[Agent-{self.agent_id}] 获取价格失败：{e}")
            return None
    
    def analyze_market(self, okx) -> Dict:
        """量子级市场分析"""
        try:
            # 获取 K 线
            ohlcv = okx.fetch_ohlcv(self.symbol, '1m', limit=50)
            if not ohlcv or len(ohlcv) < 20:
                return {'signal': 'HOLD', 'rsi': 50, 'ma_dev': 0}
            
            closes = [c[4] for c in ohlcv]
            current_price = closes[-1]
            
            # RSI (快速)
            rsi = self.calculate_rsi(closes, 7)
            
            # MA 偏离
            ma20 = sum(closes[-20:]) / 20
            ma_dev = (current_price - ma20) / ma20
            
            # 波动率
            volatility = (max(closes[-10:]) - min(closes[-10:])) / min(closes[-10:])
            
            # 信号生成 (量子级敏感)
            signal = 'HOLD'
            if rsi < 25 and ma_dev < -0.001:  # 超卖 + 低于 MA
                signal = 'LONG'
            elif rsi > 75 and ma_dev > 0.001:  # 超买 + 高于 MA
                signal = 'SHORT'
            elif volatility > self.trigger_threshold:  # 高波动突破
                if closes[-1] > closes[-2]:
                    signal = 'LONG'
                else:
                    signal = 'SHORT'
            
            return {
                'signal': signal,
                'rsi': rsi,
                'ma_dev': ma_dev * 100,
                'volatility': volatility * 100,
                'price': current_price
            }
        except Exception as e:
            print(f"[Agent-{self.agent_id}] 分析失败：{e}")
            return {'signal': 'HOLD', 'rsi': 50, 'ma_dev': 0, 'price': 0}
    
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
        rs = avg_gain / avg_loss
        return 100.0 - (100.0 / (1.0 + rs))
    
    def execute_trade(self, okx, signal: str, price: float):
        """执行交易 (模拟模式)"""
        if self.position is not None:
            # 检查出场
            side = self.position['side']
            entry = self.position['entry_price']
            
            if side == 'LONG':
                pnl_pct = (price - entry) / entry
            else:
                pnl_pct = (entry - price) / entry
            
            # 止盈止损
            if pnl_pct >= self.take_profit_pct or pnl_pct <= -self.stop_loss_pct:
                # 平仓
                pnl = self.balance * pnl_pct * self.leverage
                self.balance += pnl
                self.total_pnl += pnl
                
                result = 'WIN' if pnl > 0 else 'LOSS'
                if pnl > 0:
                    self.win_count += 1
                else:
                    self.loss_count += 1
                
                self.trades.append({
                    'symbol': self.symbol,
                    'side': side,
                    'entry': entry,
                    'exit': price,
                    'pnl': pnl,
                    'result': result,
                    'time': datetime.now().isoformat()
                })
                
                emoji = '✅' if pnl > 0 else '❌'
                print(f"[Agent-{self.agent_id}] {emoji} 平仓 {side} | PnL: ${pnl:.4f} ({pnl_pct*100:.2f}%) | 余额：${self.balance:.4f}")
                self.position = None
        
        else:
            # 开仓
            if signal in ['LONG', 'SHORT']:
                self.position = {
                    'symbol': self.symbol,
                    'side': signal,
                    'entry_price': price,
                    'entry_time': datetime.now().isoformat()
                }
                emoji = '🟢' if signal == 'LONG' else '🔴'
                print(f"[Agent-{self.agent_id}] {emoji} 开仓 {signal} @ ${price:.2f} ({self.leverage}x)")
    
    def run(self, okx):
        """主交易循环"""
        print(f"[Agent-{self.agent_id}] 🚀 启动 | {self.symbol} | {self.leverage}x | ${self.balance:.4f}")
        
        while self.running:
            self.scan_count += 1
            
            # 市场分析
            analysis = self.analyze_market(okx)
            
            if analysis['price'] > 0:
                # 执行交易
                self.execute_trade(okx, analysis['signal'], analysis['price'])
                
                # 定期汇报 (每 30 秒)
                if (datetime.now() - self.last_report).total_seconds() > 30:
                    self.report_status()
                    self.last_report = datetime.now()
            
            # 量子级频率 (每 3-5 秒扫描)
            time.sleep(random.uniform(3, 5))
    
    def report_status(self):
        """汇报状态"""
        roi = ((self.balance - self.initial_balance) / self.initial_balance) * 100
        win_rate = (self.win_count / (self.win_count + self.loss_count) * 100) if (self.win_count + self.loss_count) > 0 else 0
        
        print(f"[Agent-{self.agent_id}] 📊 状态 | 扫描:{self.scan_count} | 交易:{len(self.trades)} | 胜率:{win_rate:.1f}% | PnL:${self.total_pnl:.4f} ({roi:+.2f}%) | 余额:${self.balance:.4f}")
    
    def stop(self):
        """停止智能体"""
        self.running = False


class QuantumHive:
    """量子智能体蜂巢管理系统"""
    
    def __init__(self, initial_capital_per_agent: float = 10.0, 
                 max_agents: int = 10, leverage_range: tuple = (25, 50)):
        self.agents: List[QuantumAgent] = []
        self.initial_capital_per_agent = initial_capital_per_agent
        self.max_agents = max_agents
        self.leverage_range = leverage_range
        self.total_capital = 0.0
        self.running = True
        self.start_time = datetime.now()
        
        # OKX 初始化
        try:
            with open('okx_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self.okx = ccxt.okx({
                'apiKey': config.get('api_key', ''),
                'secret': config.get('secret_key', ''),
                'password': config.get('passphrase', ''),
                'enableRateLimit': True,
                'options': {'defaultType': 'swap'},
                'timeout': 30000,
            })
            self.okx.set_sandbox_mode(True)
            self.okx.session.trust_env = False
            self.okx.session.proxies = {}
            print("✅ OKX 测试网连接初始化")
        except Exception as e:
            print(f"⚠️ OKX 初始化失败：{e}")
            self.okx = None
        
        # 交易对池
        self.symbol_pool = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT']
    
    def spawn_agent(self, symbol: str = None) -> QuantumAgent:
        """创建新智能体"""
        if len(self.agents) >= self.max_agents:
            print(f"⚠️ 已达到最大智能体数量：{self.max_agents}")
            return None
        
        symbol = symbol or random.choice(self.symbol_pool)
        leverage = random.randint(self.leverage_range[0], self.leverage_range[1])
        
        agent_id = len(self.agents) + 1
        agent = QuantumAgent(
            agent_id=agent_id,
            symbol=symbol,
            leverage=leverage,
            initial_balance=self.initial_capital_per_agent,
            trigger_threshold=random.uniform(0.0005, 0.001)  # 0.05%-0.1%
        )
        
        self.agents.append(agent)
        self.total_capital += self.initial_capital_per_agent
        
        print(f"🆕 智能体#{agent_id} 创建 | {symbol} | {leverage}x | ${self.initial_capital_per_agent:.2f}")
        return agent
    
    def spawn_swarm(self, count: int = 5):
        """批量创建智能体群"""
        print(f"\n🐝 创建智能体群：{count}个")
        for i in range(count):
            self.spawn_agent()
            time.sleep(0.5)
    
    def run_agent(self, agent: QuantumAgent):
        """运行单个智能体"""
        if self.okx:
            agent.run(self.okx)
        else:
            print(f"[Agent-{agent.agent_id}] ⚠️ OKX 未连接，使用模拟模式")
            # 模拟价格运行
            agent.running = True
            while agent.running:
                agent.scan_count += 1
                # 模拟价格波动
                mock_price = random.uniform(95000, 96000) if 'BTC' in agent.symbol else random.uniform(2500, 2600)
                signal = random.choice(['LONG', 'SHORT', 'HOLD', 'HOLD'])
                agent.execute_trade(None, signal, mock_price)
                
                if (datetime.now() - agent.last_report).total_seconds() > 30:
                    agent.report_status()
                    agent.last_report = datetime.now()
                
                time.sleep(random.uniform(3, 5))
    
    def hive_status(self):
        """蜂巢整体状态"""
        total_balance = sum(a.balance for a in self.agents)
        total_pnl = sum(a.total_pnl for a in self.agents)
        total_trades = sum(len(a.trades) for a in self.agents)
        total_wins = sum(a.win_count for a in self.agents)
        total_losses = sum(a.loss_count for a in self.agents)
        
        win_rate = (total_wins / (total_wins + total_losses) * 100) if (total_wins + total_losses) > 0 else 0
        roi = ((total_balance - self.total_capital) / self.total_capital) * 100
        
        runtime = datetime.now() - self.start_time
        
        print("\n" + "="*70)
        print(f"🐝 Web3Million 量子蜂巢状态 | 运行时间：{runtime}")
        print("="*70)
        print(f"智能体数量：{len(self.agents)}/{self.max_agents}")
        print(f"总资金：${total_balance:.4f} (初始：${self.total_capital:.4f})")
        print(f"总 PnL: ${total_pnl:.4f} ({roi:+.2f}%)")
        print(f"总交易：{total_trades} | 胜率：{win_rate:.1f}%")
        print(f"活跃智能体：{sum(1 for a in self.agents if a.running)}")
        print("="*70 + "\n")
    
    def run(self):
        """启动蜂巢"""
        print("\n" + "="*70)
        print("🚀 Web3Million 量子高频交易蜂巢 v1.0")
        print("="*70)
        print(f"启动时间：{self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"初始资金/智能体：${self.initial_capital_per_agent}")
        print(f"杠杆范围：{self.leverage_range[0]}x-{self.leverage_range[1]}x")
        print(f"最大智能体：{self.max_agents}")
        print(f"触发阈值：0.05%-0.1%")
        print("="*70 + "\n")
        
        # 创建初始智能体群
        self.spawn_swarm(5)
        
        # 启动智能体线程
        threads = []
        for agent in self.agents:
            t = threading.Thread(target=self.run_agent, args=(agent,), daemon=True)
            t.start()
            threads.append(t)
            time.sleep(1)
        
        # 主循环：监控和汇报
        report_interval = 60  # 每 60 秒汇报
        auto_spawn_interval = 300  # 每 5 分钟创建新智能体
        last_report = datetime.now()
        last_spawn = datetime.now()
        
        while self.running:
            time.sleep(1)
            
            # 定期汇报
            if (datetime.now() - last_report).total_seconds() > report_interval:
                self.hive_status()
                last_report = datetime.now()
            
            # 自动扩容
            if (datetime.now() - last_spawn).total_seconds() > auto_spawn_interval:
                if len(self.agents) < self.max_agents:
                    self.spawn_agent()
                    agent = self.agents[-1]
                    t = threading.Thread(target=self.run_agent, args=(agent,), daemon=True)
                    t.start()
                last_spawn = datetime.now()
    
    def stop(self):
        """停止所有智能体"""
        print("\n🛑 停止所有智能体...")
        self.running = False
        for agent in self.agents:
            agent.stop()


if __name__ == '__main__':
    try:
        hive = QuantumHive(
            initial_capital_per_agent=10.0,
            max_agents=10,
            leverage_range=(25, 50)
        )
        hive.run()
    except KeyboardInterrupt:
        print("\n\n👋 手动停止")
        if 'hive' in dir():
            hive.stop()
    except Exception as e:
        print(f"\n❌ 错误：{e}")
        import traceback
        traceback.print_exc()
