#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million 改进版交易系统 v2.0
基于亏损分析 + OpenClaw自我进化机制
"""
import ccxt
import time
import json
from datetime import datetime
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class ImprovedTradingSystem:
    """改进版交易系统 - 吸收OpenClaw自我进化机制"""
    
    def __init__(self):
        # 交易所
        self.exchange = ccxt.okx({
            'apiKey': 'b71ee824-5524-4cde-b818-b8e294c27d56',
            'secret': '76122A8879980469F474F042135584DB',
            'password': 'Qian159.',
            'testnet': True
        })
        
        # 核心参数 (v2.0改进)
        self.initial_capital = 4776.38  # 当前USDT
        self.current_capital = self.initial_capital
        
        # 改进1: 不做高频剥头皮 -> 改为趋势跟随
        self.trend_threshold = 0.005  # 0.5%趋势确认
        self.risk_per_trade = 0.02  # 2%风险
        self.position_size = 0.1  # 10%仓位
        
        # 改进2: 严格止损止盈
        self.stop_loss = 0.015  # 1.5%止损
        self.take_profit = 0.03  # 3%止盈
        
        # 改进3: 趋势指标
        self.ma_short = 5   # 5周期均线
        self.ma_long = 20  # 20周期均线
        
        # 改进4: 状态机 (类似OpenClaw session)
        self.state = 'IDLE'  # IDLE, WATCHING, POSITION, CLOSED
        self.entry_price = 0
        self.position_amount = 0
        self.trades = []
        
        # 自我进化数据
        self.performance_history = []
        self.strategy_params = {
            'trend_threshold': 0.005,
            'stop_loss': 0.015,
            'take_profit': 0.03,
            'position_size': 0.1
        }
        
    def get_ohlcv(self, symbol, timeframe='15m', limit=30):
        """获取K线数据"""
        try:
            return self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        except Exception as e:
            print(f"获取K线失败: {e}")
            return None
    
    def calculate_ma(self, closes, period):
        """计算移动平均线"""
        if len(closes) < period:
            return None
        return sum(closes[-period:]) / period
    
    def detect_trend(self, ohlcv):
        """检测趋势 - 改进核心"""
        if not ohlcv or len(ohlcv) < self.ma_long:
            return 'neutral'
        
        closes = [c[4] for c in ohlcv]
        
        ma5 = self.calculate_ma(closes, self.ma_short)
        ma20 = self.calculate_ma(closes, self.ma_long)
        
        if not ma5 or not ma20:
            return 'neutral'
        
        # 趋势判断
        price = closes[-1]
        trend_strength = (ma5 - ma20) / ma20
        
        if trend_strength > self.trend_threshold:
            return 'bullish'
        elif trend_strength < -self.trend_threshold:
            return 'bearish'
        return 'neutral'
    
    def get_funding_rate(self, symbol):
        """获取资金费率 (合约)"""
        try:
            # 尝试获取永续合约资金费率
            if ':' not in symbol:
                symbol = symbol.replace('/', '/USDT:')
            market = self.exchange.fetch_market(symbol)
            return market.get('info', {}).get('fundingRate', 0)
        except:
            return 0
    
    def calculate_position_value(self):
        """计算仓位价值"""
        return self.current_capital * self.position_size
    
    def execute_buy(self, symbol, amount):
        """执行买入"""
        try:
            order = self.exchange.create_market_buy_order(symbol, amount)
            return order
        except Exception as e:
            print(f"买入失败: {e}")
            return None
    
    def execute_sell(self, symbol, amount):
        """执行卖出"""
        try:
            order = self.exchange.create_market_sell_order(symbol, amount)
            return order
        except Exception as e:
            print(f"卖出失败: {e}")
            return None
    
    def check_stop_loss(self, current_price):
        """检查止损"""
        if self.state != 'POSITION':
            return False
        
        pnl_pct = (current_price - self.entry_price) / self.entry_price
        
        # 亏损超过止损线
        if pnl_pct <= -self.stop_loss:
            print(f"🛑 触发止损! PnL: {pnl_pct*100:.2f}%")
            return True
        return False
    
    def check_take_profit(self, current_price):
        """检查止盈"""
        if self.state != 'POSITION':
            return False
        
        pnl_pct = (current_price - self.entry_price) / self.entry_price
        
        # 盈利超过止盈线
        if pnl_pct >= self.take_profit:
            print(f"🎯 触发止盈! PnL: {pnl_pct*100:.2f}%")
            return True
        return False
    
    def analyze_and_trade(self, symbol='ETH/USDT'):
        """分析并交易 - 核心逻辑"""
        print(f"\n{'='*50}")
        print(f"🔍 分析 {symbol}")
        print(f"{'='*50}")
        
        # 1. 获取数据
        ohlcv = self.get_ohlcv(symbol)
        if not ohlcv:
            print("❌ 无法获取数据")
            return
        
        closes = [c[4] for c in ohlcv]
        current_price = closes[-1]
        
        # 2. 检测趋势
        trend = self.detect_trend(ohlcv)
        ma5 = self.calculate_ma(closes, self.ma_short)
        ma20 = self.calculate_ma(closes, self.ma_long)
        
        print(f"📊 当前价格: ${current_price}")
        print(f"📈 MA5: ${ma5:.2f}, MA20: ${ma20:.2f}")
        print(f"🎯 趋势: {trend}")
        print(f"💰 当前资金: ${self.current_capital:.2f}")
        
        # 3. 状态机交易
        if self.state == 'IDLE':
            if trend == 'bullish':
                # 入场
                amount = (self.current_capital * self.position_size) / current_price
                order = self.execute_buy(symbol, amount)
                if order:
                    self.state = 'POSITION'
                    self.entry_price = current_price
                    self.position_amount = amount
                    print(f"✅ 做多入场 @ ${current_price}")
                    
        elif self.state == 'POSITION':
            # 检查止盈止损
            if self.check_stop_loss(current_price) or self.check_take_profit(current_price):
                # 平仓
                order = self.execute_sell(symbol, self.position_amount)
                if order:
                    pnl = (current_price - self.entry_price) * self.position_amount
                    self.current_capital += pnl
                    
                    # 记录交易
                    self.trades.append({
                        'entry': self.entry_price,
                        'exit': current_price,
                        'pnl': pnl,
                        'pnl_pct': (current_price - self.entry_price) / self.entry_price * 100
                    })
                    
                    print(f"✅ 平仓 @ ${current_price}, PnL: ${pnl:.2f}")
                    self.state = 'IDLE'
        
        # 4. 自我进化 - 分析表现
        self.evolve()
        
    def evolve(self):
        """自我进化 - 类似OpenClaw学习机制"""
        if len(self.trades) < 3:
            return
        
        recent_pnls = [t['pnl'] for t in self.trades[-5:]]
        avg_pnl = sum(recent_pnls) / len(recent_pnls)
        
        print(f"\n🧬 自我进化分析:")
        print(f"  近5笔平均P&L: ${avg_pnl:.2f}")
        
        # 如果连续亏损，调整参数
        if avg_pnl < -1:
            print("  ⚠️ 连续亏损 - 收紧止损")
            self.strategy_params['stop_loss'] = max(0.01, self.strategy_params['stop_loss'] * 0.8)
        elif avg_pnl > 5:
            print("  📈 表现良好 - 保持参数")
        
        print(f"  当前参数: {self.strategy_params}")
    
    def run(self, iterations=10):
        """运行交易系统"""
        print("🚀 启动改进版交易系统 v2.0")
        print(f"💰 初始资金: ${self.current_capital}")
        print(f"🎯 策略: 趋势跟随 + 严格止盈止损")
        
        for i in range(iterations):
            print(f"\n--- 第{i+1}轮 ---")
            self.analyze_and_trade()
            
            # 每轮间隔
            time.sleep(5)
            
            # 每3轮报告
            if (i+1) % 3 == 0:
                self.print_report()
        
        self.print_report()
        
    def print_report(self):
        """输出报告"""
        print("\n" + "="*50)
        print("📊 交易报告")
        print("="*50)
        print(f"💰 最终资金: ${self.current_capital:.2f}")
        print(f"📈 总收益: ${self.current_capital - self.initial_capital:.2f}")
        print(f"📊 收益率: {((self.current_capital/self.initial_capital)-1)*100:.2f}%")
        print(f"🔢 总交易数: {len(self.trades)}")
        
        if self.trades:
            wins = [t for t in self.trades if t['pnl'] > 0]
            print(f"🎯 胜率: {len(wins)/len(self.trades)*100:.1f}%")
        
        print("="*50)


if __name__ == "__main__":
    system = ImprovedTradingSystem()
    system.run(iterations=5)
