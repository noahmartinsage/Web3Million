#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million Quantum Single v1.0 - 简化单进程版
功能特性:
- 单线程轮询，Windows 兼容
- 分批止盈策略 (3%/5%/8% 三档)
- 动态风险控制
- 7x24 小时稳定运行
"""
import sys
import io
import os
import json
import time
import random
from datetime import datetime
from typing import Dict, List, Optional

# 清除代理
for var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    os.environ.pop(var, None)

try:
    import ccxt
except ImportError:
    print("Error: ccxt not found. Install with: pip install ccxt")
    sys.exit(1)

class QuantumSingleAgent:
    """单进程量子智能体 - 支持分批止盈"""
    
    def __init__(self, symbol: str, leverage: int = 30, initial_balance: float = 10.0):
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
        
        # 初始化 OKX
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
            print(f"[{self.symbol}] OKX 连接成功")
        except Exception as e:
            print(f"[{self.symbol}] OKX 连接失败：{e}")
            raise
    
    def analyze_market(self) -> Dict:
        """市场分析"""
        try:
            ohlcv = self.okx.fetch_ohlcv(self.symbol, '1m', limit=50)
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
        """检查分批止盈条件"""
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
            
            if pnl_pct >= level_pnl_pct:
                sell_ratio_of_remaining = sell_ratio * remaining_ratio
                if sell_ratio_of_remaining > 0:
                    actions.append({
                        'type': 'PARTIAL_CLOSE',
                        'ratio': sell_ratio_of_remaining,
                        'reason': f'止盈{level_pnl_pct*self.leverage*100:.0f}%',
                        'pnl_pct': pnl_pct
                    })
                    remaining_ratio -= sell_ratio_of_remaining
        
        # 检查止损
        if pnl_pct <= -self.stop_loss_pct * self.leverage:
            actions.append({
                'type': 'FULL_CLOSE',
                'reason': f'止损{-self.stop_loss_pct*100:.1f}%',
                'pnl_pct': pnl_pct
            })
        
        return actions
    
    def execute_trade(self, signal: str, price: float):
        """执行交易 - 支持分批止盈"""
        if self.position is not None and self.position_size > 0:
            # 检查止盈止损
            actions = self.check_batch_take_profit(price)
            
            for action in actions:
                if action['type'] == 'PARTIAL_CLOSE':
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
                    
                    emoji = '[OK]' if pnl > 0 else '[X]'
                    print(f"[{self.symbol}] {emoji} 分批{action['reason']} | PnL: ${pnl:.4f} | 余额：${self.balance:.4f}")
                    
                    if self.position_size <= 0.001:
                        self.position = None
                        self.position_size = 0
                        break
                
                elif action['type'] == 'FULL_CLOSE':
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
                    
                    emoji = '[OK]' if pnl > 0 else '[X]'
                    print(f"[{self.symbol}] {emoji} {action['reason']} | PnL: ${pnl:.4f} | 余额：${self.balance:.4f}")
                    break
        
        # 开新仓
        if self.position is None and signal in ['LONG', 'SHORT']:
            position_value = self.balance * 0.5
            self.position_size = (position_value * self.leverage) / price
            self.entry_price = price
            self.position = {'side': signal, 'entry_price': price, 'entry_time': datetime.now().isoformat()}
            
            emoji = '[LONG]' if signal == 'LONG' else '[SHORT]'
            print(f"[{self.symbol}] {emoji} 开仓 @ ${price:.2f} ({self.leverage}x) | 数量：{self.position_size:.4f}")
    
    def run(self):
        """运行智能体"""
        print(f"[{self.symbol}] 启动 | {self.leverage}x | ${self.balance:.2f}")
        
        while self.running:
            try:
                data = self.analyze_market()
                self.scan_count += 1
                
                if data.get('signal') and data.get('price'):
                    self.execute_trade(data['signal'], data['price'])
                
                # 定期报告
                if (datetime.now() - self.last_report).total_seconds() > 60:
                    print(f"[{self.symbol}] 扫描：{self.scan_count} | PnL: ${self.total_pnl:.4f} | 余额：${self.balance:.4f}")
                    self.last_report = datetime.now()
                
                time.sleep(random.uniform(5, 10))
            except Exception as e:
                print(f"[{self.symbol}] 错误：{e}")
                time.sleep(10)
    
    def stop(self):
        self.running = False


if __name__ == '__main__':
    print("=" * 80)
    print("Web3Million Quantum Single v1.0 - 简化单进程版")
    print(f"启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    try:
        # 创建单个智能体 (BTC)
        agent = QuantumSingleAgent(
            symbol='BTC/USDT:USDT',
            leverage=30,
            initial_balance=10.0
        )
        
        # 运行
        agent.run()
    except KeyboardInterrupt:
        print("\n停止运行")
    except Exception as e:
        print(f"异常：{e}")
        import traceback
        traceback.print_exc()
