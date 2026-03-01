#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million SimTrader v1.0 - 模拟交易模式
本地生成价格数据，测试 v7.2 策略逻辑
"""
import random
import math
import time
import json
from datetime import datetime

class SimTrader:
    def __init__(self):
        # 初始配置
        self.initial_balance = 670.0  # USDT
        self.balance = self.initial_balance
        self.leverage = 20
        self.stop_loss_pct = 0.05 / self.leverage  # 5% 账户风险
        self.take_profit_pct = 0.15 / self.leverage  # 15% 账户风险
        self.position_pct = 0.02  # 2% 仓位
        self.max_position = 30  # 最大 $30
        
        # 模拟价格 (初始值)
        self.prices = {
            'BTC': 95000.0,
            'ETH': 2500.0,
            'SOL': 180.0
        }
        self.price_history = {k: [v] for k, v in self.prices.items()}
        
        # 交易状态
        self.position = None
        self.trades = []
        self.total_pnl = 0.0
        self.scan_count = 0
        self.session_start = datetime.now()
        
        # 模拟参数
        self.volatility = 0.002  # 0.2% 波动率
        self.trend_bias = 0.0  # 无偏向
        
        print("=" * 60)
        print("Web3Million SimTrader v1.0 - 模拟模式")
        print("=" * 60)
        print(f"启动时间：{self.session_start.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"初始余额：${self.initial_balance:.2f}")
        print(f"杠杆：{self.leverage}x")
        print(f"止损：{self.stop_loss_pct*100/self.leverage:.2f}% (价格)")
        print(f"止盈：{self.take_profit_pct*100/self.leverage:.2f}% (价格)")
        print("=" * 60)
    
    def generate_price(self, symbol):
        """生成模拟价格 (随机游走 + 趋势)"""
        base_price = self.prices[symbol]
        
        # 随机波动
        change = random.gauss(self.trend_bias, self.volatility)
        new_price = base_price * (1 + change)
        
        # 确保价格为正
        new_price = max(new_price, base_price * 0.9)
        
        self.prices[symbol] = new_price
        self.price_history[symbol].append(new_price)
        
        # 保持历史记录长度
        if len(self.price_history[symbol]) > 200:
            self.price_history[symbol].pop(0)
        
        return new_price
    
    def calculate_rsi(self, prices, period=14):
        """计算 RSI"""
        if len(prices) < period + 1:
            return 50.0
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100.0 - (100.0 / (1.0 + rs))
    
    def calculate_ma(self, prices, period):
        """计算移动平均"""
        if len(prices) < period:
            return prices[-1] if prices else 0
        return sum(prices[-period:]) / period
    
    def check_signals(self, symbol):
        """检查交易信号"""
        prices = self.price_history[symbol]
        current_price = prices[-1]
        
        # 技术指标
        rsi = self.calculate_rsi(prices)
        ma5 = self.calculate_ma(prices, 5)
        ma20 = self.calculate_ma(prices, 20)
        
        # 趋势判断
        trend = 'BULLISH' if ma5 > ma20 else 'BEARISH'
        
        # 交易信号
        long_signal = rsi < 32 and ma5 > ma20
        short_signal = rsi > 68 and ma5 < ma20
        
        return {
            'symbol': symbol,
            'price': current_price,
            'rsi': rsi,
            'ma5': ma5,
            'ma20': ma20,
            'trend': trend,
            'signal': 'LONG' if long_signal else ('SHORT' if short_signal else 'HOLD')
        }
    
    def execute_trade(self, symbol, side, price):
        """执行交易"""
        position_size = min(self.balance * self.position_pct, self.max_position)
        
        self.position = {
            'symbol': symbol,
            'side': side,
            'entry_price': price,
            'size': position_size,
            'open_time': datetime.now()
        }
        
        self.trades.append({
            'type': 'OPEN',
            'symbol': symbol,
            'side': side,
            'price': price,
            'size': position_size,
            'time': datetime.now()
        })
        
        return True
    
    def check_position(self, symbol, current_price):
        """检查持仓盈亏"""
        if not self.position or self.position['symbol'] != symbol:
            return
        
        entry = self.position['entry_price']
        side = self.position['side']
        
        # 计算盈亏
        if side == 'LONG':
            pnl_pct = (current_price - entry) / entry
        else:
            pnl_pct = (entry - current_price) / entry
        
        pnl_usdt = pnl_pct * self.position['size'] * self.leverage
        
        # 检查止损止盈
        if pnl_pct <= -self.stop_loss_pct:
            self.close_position(current_price, 'STOP LOSS')
        elif pnl_pct >= self.take_profit_pct:
            self.close_position(current_price, 'TAKE PROFIT')
        
        return pnl_pct, pnl_usdt
    
    def close_position(self, current_price, reason):
        """平仓"""
        if not self.position:
            return
        
        entry = self.position['entry_price']
        side = self.position['side']
        
        if side == 'LONG':
            pnl_pct = (current_price - entry) / entry
        else:
            pnl_pct = (entry - current_price) / entry
        
        pnl_usdt = pnl_pct * self.position['size'] * self.leverage
        self.balance += pnl_usdt
        self.total_pnl += pnl_usdt
        
        self.trades.append({
            'type': 'CLOSE',
            'symbol': self.position['symbol'],
            'side': side,
            'entry': entry,
            'exit': current_price,
            'pnl': pnl_usdt,
            'reason': reason,
            'time': datetime.now()
        })
        
        print(f"\n{'='*40}")
        print(f"[平仓] {self.position['symbol']}")
        print(f"方向：{side} | 入场：${entry:,.2f} | 出场：${current_price:,.2f}")
        print(f"原因：{reason}")
        print(f"盈亏：${pnl_usdt:.2f} ({pnl_pct*100:.2f}%)")
        print(f"总盈亏：${self.total_pnl:.2f}")
        print(f"余额：${self.balance:.2f}")
        print(f"{'='*40}")
        
        self.position = None
    
    def run(self, duration_minutes=30):
        """运行模拟交易"""
        print(f"\n[START] 开始模拟交易...")
        print(f"运行时长：{duration_minutes} 分钟")
        print(f"扫描间隔：5 秒\n")
        
        end_time = time.time() + (duration_minutes * 60)
        
        while time.time() < end_time:
            try:
                self.scan_count += 1
                timestamp = datetime.now().strftime('%H:%M:%S')
                
                print(f"\n{'='*60}")
                print(f"[扫描 #{self.scan_count}] {timestamp}")
                print(f"{'='*60}")
                
                # 生成新价格并扫描
                for symbol in ['BTC', 'ETH', 'SOL']:
                    price = self.generate_price(symbol)
                    info = self.check_signals(symbol)
                    
                    print(f"\n{symbol}")
                    print(f"  价格：${price:,.2f}")
                    print(f"  RSI: {info['rsi']:.2f}")
                    print(f"  MA5: ${info['ma5']:,.2f} | MA20: ${info['ma20']:,.2f}")
                    print(f"  趋势：{info['trend']}")
                    print(f"  信号：{info['signal']}")
                    
                    # 检查持仓
                    if self.position and self.position['symbol'] == symbol:
                        pnl_pct, pnl_usdt = self.check_position(symbol, price)
                        print(f"  持仓盈亏：{pnl_pct*100:.2f}% (${pnl_usdt:.2f})")
                    
                    # 执行交易
                    if info['signal'] in ['LONG', 'SHORT'] and not self.position:
                        print(f"  >>> 执行 {info['signal']} 交易!")
                        self.execute_trade(symbol, info['signal'], price)
                
                print(f"\n[BALANCE] 当前余额：${self.balance:.2f}")
                print(f"[PNL] 总盈亏：${self.total_pnl:.2f}")
                
                # 等待下次扫描
                time.sleep(5)
                
            except KeyboardInterrupt:
                print(f"\n\n[STOP] 手动停止")
                break
            except Exception as e:
                print(f"\n[ERROR] {e}")
                time.sleep(5)
        
        # 最终报告
        self.print_summary()
    
    def print_summary(self):
        """打印总结报告"""
        elapsed = datetime.now() - self.session_start
        
        print(f"\n{'='*60}")
        print("交易会话总结")
        print(f"{'='*60}")
        print(f"运行时间：{elapsed}")
        print(f"扫描次数：{self.scan_count}")
        print(f"交易数量：{len([t for t in self.trades if t['type'] == 'OPEN'])}")
        print(f"总盈亏：${self.total_pnl:.2f}")
        print(f"收益率：{(self.total_pnl/self.initial_balance)*100:.2f}%")
        print(f"最终余额：${self.balance:.2f}")
        print(f"{'='*60}")
        
        # 保存记录
        summary = {
            'start_time': self.session_start.isoformat(),
            'end_time': datetime.now().isoformat(),
            'scans': self.scan_count,
            'trades': len([t for t in self.trades if t['type'] == 'OPEN']),
            'total_pnl': self.total_pnl,
            'final_balance': self.balance,
            'roi_pct': (self.total_pnl/self.initial_balance)*100
        }
        
        with open('sim_trader_result.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n[OK] 结果已保存到 sim_trader_result.json")

if __name__ == '__main__':
    trader = SimTrader()
    trader.run(duration_minutes=10)  # 运行 10 分钟
