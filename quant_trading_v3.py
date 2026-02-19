#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million 量化交易系统 v3.0 - 完整内化quant-trading-bot能力
五大核心模块：数据采集 → 指标计算 → 交易决策 → 交易执行 → 风控监控
"""
import ccxt
import pandas as pd
import numpy as np
import time
import json
from datetime import datetime
from scipy.signal import argrelextrema
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class QuantTradingSystemV3:
    """量化交易系统 v3.0 - 完整内化quant-trading-bot"""
    
    def __init__(self):
        # 交易所配置
        self.exchange = ccxt.okx({
            'apiKey': 'b71ee824-5524-4cde-b818-b8e294c27d56',
            'secret': '76122A8879980469F474F042135584DB',
            'password': 'Qian159.',
            'testnet': True
        })
        
        # ========== 核心参数配置 ==========
        self.config = {
            'symbol': 'ETH/USDT',
            'timeframe': '15m',
            'initial_capital': 4776.38,
            'current_capital': 4776.38,
        }
        
        # 风控参数 (来自quant-trading-bot)
        self.risk_controls = {
            'MIN_ORDER_SIZE': 1,       # 最小1U
            'MAX_ORDER_SIZE': 100,     # 最大100U
            'STOP_LOSS_RATE': 0.01,    # 1%止损
            'TAKE_PROFIT_RATE': 0.02,  # 2%最低止盈 (止损的2倍)
            'MAX_DAILY_LOSS': 0.05,   # 单日5%亏损暂停
            'MAX_POSITION_RATIO': 0.1,  # 10%最大持仓
        }
        
        # 指标权重 (来自quant-trading-bot)
        self.weights = {
            'macd': 0.10,
            'rsi': 0.10,
            'kdj': 0.10,
            'volume': 0.05,
            'ma': 0.05,
            'divergence': 0.05,
        }
        
        # 指标周期
        self.periods = {
            'RSI': 14,
            'MACD_FAST': 12,
            'MACD_SLOW': 26,
            'MACD_SIGNAL': 9,
            'MA_SHORT': 5,
            'MA_LONG': 20,
        }
        
        # 状态管理
        self.state = 'IDLE'  # IDLE, WATCHING, POSITION
        self.position = None
        self.entry_price = 0
        self.trades = []
        self.daily_pnl = 0
        
    # ==================== 模块1: 数据采集 ====================
    def collect_market_data(self, limit=100):
        """数据采集模块 - 采集K线数据"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(
                self.config['symbol'], 
                self.config['timeframe'], 
                limit=limit
            )
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            print(f"数据采集失败: {e}")
            return pd.DataFrame()
    
    # ==================== 模块2: 指标计算 ====================
    def calculate_indicators(self, df):
        """指标计算模块 - 计算所有技术指标"""
        if df.empty:
            return df
        
        closes = df['close']
        highs = df['high']
        lows = df['low']
        
        # MACD
        exp1 = closes.ewm(span=self.periods['MACD_FAST']).mean()
        exp2 = closes.ewm(span=self.periods['MACD_SLOW']).mean()
        df['macd_diff'] = exp1 - exp2
        df['macd_dea'] = df['macd_diff'].ewm(span=self.periods['MACD_SIGNAL']).mean()
        df['macd_bar'] = 2 * (df['macd_diff'] - df['macd_dea'])
        
        # RSI
        delta = closes.diff()
        gain = delta.where(delta > 0, 0).rolling(window=self.periods['RSI']).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.periods['RSI']).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # KDJ
        period = 9
        lowest_low = lows.rolling(window=period).min()
        highest_high = highs.rolling(window=period).max()
        rsv = (closes - lowest_low) / (highest_high - lowest_low) * 100
        df['kd_k'] = rsv.ewm(com=2).mean()
        df['kd_d'] = df['kd_k'].ewm(com=2).mean()
        df['kd_j'] = 3 * df['kd_k'] - 2 * df['kd_d']
        
        # 均线系统
        df['ma5'] = closes.rolling(window=self.periods['MA_SHORT']).mean()
        df['ma20'] = closes.rolling(window=self.periods['MA_LONG']).mean()
        
        # 成交量均线
        df['vol_ma'] = df['volume'].rolling(window=5).mean()
        
        # 计算各项得分
        df = self.calculate_scores(df)
        
        return df
    
    def calculate_scores(self, df):
        """计算各项指标得分"""
        if len(df) < 30:
            return df
        
        latest = df.iloc[-1]
        
        # MACD得分
        if latest['macd_diff'] > latest['macd_dea']:
            df['macd_score'] = 10
        else:
            df['macd_score'] = -10
        
        # RSI得分 (超卖看涨，超买看跌)
        if latest['rsi'] <= 30:
            df['rsi_score'] = 10
        elif latest['rsi'] >= 70:
            df['rsi_score'] = -10
        else:
            df['rsi_score'] = 0
        
        # KDJ得分
        if latest['kd_j'] <= 20:
            df['kdj_score'] = 10  # 超卖
        elif latest['kd_j'] >= 80:
            df['kdj_score'] = -10  # 超买
        elif latest['kd_k'] > latest['kd_d']:
            df['kdj_score'] = 5   # 金叉
        elif latest['kd_k'] < latest['kd_d']:
            df['kdj_score'] = -5  # 死叉
        else:
            df['kdj_score'] = 0
        
        # 均线得分
        if latest['ma5'] > latest['ma20']:
            df['ma_score'] = 10  # 多头
        else:
            df['ma_score'] = -10  # 空头
        
        # 成交量得分
        if latest['volume'] > latest['vol_ma'] * 1.5:
            df['volume_score'] = 5
        else:
            df['volume_score'] = 0
        
        return df
    
    # ==================== 模块3: 交易决策 ====================
    def calculate_composite_score(self, df):
        """交易决策模块 - 计算综合得分"""
        if len(df) < 30:
            return 0
        
        latest = df.iloc[-1]
        
        # 综合得分 = 各项指标加权求和
        score = (
            latest['macd_score'] * self.weights['macd'] +
            latest['rsi_score'] * self.weights['rsi'] +
            latest['kdj_score'] * self.weights['kdj'] +
            latest['ma_score'] * self.weights['ma'] +
            latest['volume_score'] * self.weights['volume']
        )
        
        return score
    
    def apply_veto_rules(self, df):
        """一票否决机制"""
        if len(df) < 30:
            return None
        
        latest = df.iloc[-1]
        
        # MACD顶背离 + RSI超买 = 强烈看跌
        if latest['macd_diff'] < latest['macd_dea'] and latest['rsi'] >= 70:
            return {'signal': -1, 'reason': 'MACD顶背离+RSI超买'}
        
        # MACD底背离 + RSI超卖 = 强烈看涨
        if latest['macd_diff'] > latest['macd_dea'] and latest['rsi'] <= 30:
            return {'signal': 1, 'reason': 'MACD底背离+RSI超卖'}
        
        return None
    
    def determine_signal(self, df):
        """确定交易信号"""
        # 先检查一票否决
        veto = self.apply_veto_rules(df)
        if veto:
            return veto
        
        # 计算综合得分
        score = self.calculate_composite_score(df)
        
        # 信号判定
        if score >= 30:
            return {'signal': 1, 'score': score, 'reason': '综合看涨'}
        elif score <= -30:
            return {'signal': -1, 'score': score, 'reason': '综合看跌'}
        else:
            return {'signal': 0, 'score': score, 'reason': '震荡观望'}
    
    # ==================== 模块4: 交易执行 ====================
    def execute_trade(self, signal):
        """交易执行模块"""
        if signal['signal'] == 0:
            return None
        
        symbol = self.config['symbol']
        
        # 计算仓位
        position_value = self.config['current_capital'] * self.risk_controls['MAX_POSITION_RATIO']
        amount = position_value / self.get_current_price()
        
        # 确保在允许范围内
        amount = max(0.001, min(amount, 1))
        
        try:
            if signal['signal'] == 1:  # 买入
                order = self.exchange.create_market_buy_order(symbol, amount)
                self.position = 'LONG'
                self.entry_price = self.get_current_price()
                print(f"✅ 买入开多: {amount} @ ${self.entry_price}")
            elif signal['signal'] == -1:  # 卖出
                order = self.exchange.create_market_sell_order(symbol, amount)
                self.position = 'SHORT'
                self.entry_price = self.get_current_price()
                print(f"✅ 卖出开空: {amount} @ ${self.entry_price}")
            
            return order
        except Exception as e:
            print(f"交易执行失败: {e}")
            return None
    
    def get_current_price(self):
        """获取当前价格"""
        try:
            ticker = self.exchange.fetch_ticker(self.config['symbol'])
            return ticker['last']
        except:
            return 0
    
    # ==================== 模块5: 风控监控 ====================
    def calculate_stop_loss_take_profit(self, composite_score):
        """风控模块 - 计算止盈止损 (止盈为止损的2-10倍)"""
        base_stop = self.risk_controls['STOP_LOSS_RATE']
        
        # 根据综合得分调整止盈倍数
        if composite_score >= 50:
            take_profit_multiplier = 10  # 高信心
        elif composite_score >= 30:
            take_profit_multiplier = 7
        elif composite_score >= 10:
            take_profit_multiplier = 5
        else:
            take_profit_multiplier = 3
        
        stop_loss = base_stop
        take_profit = base_stop * take_profit_multiplier
        
        return stop_loss, take_profit
    
    def check_exit_conditions(self):
        """检查退出条件"""
        if self.state != 'POSITION' or not self.position:
            return None
        
        current_price = self.get_current_price()
        if current_price == 0:
            return None
        
        # 计算盈亏
        if self.position == 'LONG':
            pnl_pct = (current_price - self.entry_price) / self.entry_price
        else:
            pnl_pct = (self.entry_price - current_price) / self.entry_price
        
        # 获取止盈止损
        score = self.calculate_composite_score(self.calculate_indicators(self.collect_market_data()))
        stop_loss, take_profit = self.calculate_stop_loss_take_profit(score)
        
        # 检查止损
        if pnl_pct <= -stop_loss:
            return {'exit': True, 'reason': '止损', 'pnl_pct': pnl_pct}
        
        # 检查止盈
        if pnl_pct >= take_profit:
            return {'exit': True, 'reason': '止盈', 'pnl_pct': pnl_pct}
        
        return None
    
    def close_position(self, reason):
        """平仓"""
        if not self.position:
            return
        
        symbol = self.config['symbol']
        
        try:
            # 获取持仓数量
            balance = self.exchange.fetch_balance()
            # 简化：假设持有ETH
            amount = balance['free'].get('ETH', 0)
            
            if amount > 0.001:
                if self.position == 'LONG':
                    order = self.exchange.create_market_sell_order(symbol, amount)
                else:
                    order = self.exchange.create_market_buy_order(symbol, amount)
                
                current_price = self.get_current_price()
                pnl = (current_price - self.entry_price) * amount if self.position == 'LONG' else (self.entry_price - current_price) * amount
                
                print(f"🔚 平仓: {self.position} @ ${current_price}, 原因: {reason}, PnL: ${pnl:.2f}")
                
                self.trades.append({
                    'entry': self.entry_price,
                    'exit': current_price,
                    'pnl': pnl,
                    'reason': reason,
                    'time': datetime.now().isoformat()
                })
                
                self.config['current_capital'] += pnl
            
            self.position = None
            self.entry_price = 0
            self.state = 'IDLE'
            
        except Exception as e:
            print(f"平仓失败: {e}")
    
    # ==================== 主循环 ====================
    def run(self, iterations=10):
        """主交易循环"""
        print("=" * 60)
        print("🚀 Web3Million 量化交易系统 v3.0 启动")
        print(f"💰 初始资金: ${self.config['current_capital']}")
        print("📊 策略: 多指标综合决策 + 严格风控")
        print("=" * 60)
        
        for i in range(iterations):
            print(f"\n--- 第{i+1}轮 ---")
            
            # 1. 数据采集
            df = self.collect_market_data()
            if df.empty:
                print("❌ 数据采集失败")
                time.sleep(5)
                continue
            
            # 2. 指标计算
            df = self.calculate_indicators(df)
            current_price = df.iloc[-1]['close']
            
            print(f"💵 价格: ${current_price:.2f}")
            print(f"📈 RSI: {df.iloc[-1]['rsi']:.1f}")
            print(f"📊 MACD: {df.iloc[-1]['macd_bar']:.4f}")
            
            # 3. 交易决策
            signal = self.determine_signal(df)
            print(f"🎯 信号: {signal}")
            
            # 4. 状态机执行
            if self.state == 'IDLE':
                if signal['signal'] != 0:
                    self.execute_trade(signal)
                    if self.position:
                        self.state = 'POSITION'
            
            elif self.state == 'POSITION':
                exit_cond = self.check_exit_conditions()
                if exit_cond:
                    self.close_position(exit_cond['reason'])
            
            # 间隔
            time.sleep(10)
            
            # 每3轮报告
            if (i+1) % 3 == 0:
                self.print_report()
        
        self.print_report()
    
    def print_report(self):
        """输出报告"""
        print("\n" + "=" * 60)
        print("📊 交易报告")
        print("=" * 60)
        print(f"💰 当前资金: ${self.config['current_capital']:.2f}")
        print(f"📈 总收益: ${self.config['current_capital'] - self.config['initial_capital']:.2f}")
        print(f"📊 收益率: {((self.config['current_capital']/self.config['initial_capital'])-1)*100:.2f}%")
        print(f"🔢 交易次数: {len(self.trades)}")
        
        if self.trades:
            wins = [t for t in self.trades if t['pnl'] > 0]
            print(f"🎯 胜率: {len(wins)/len(self.trades)*100:.1f}%")
        
        print("=" * 60)


if __name__ == "__main__":
    system = QuantTradingSystemV3()
    system.run(iterations=5)
