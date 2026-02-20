#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million 高频量化交易系统 v4.5 - 增强版
整合 GitHub 最新量化项目核心机制:
- 市场状态检测 (AgentQuant): VIX + 动量判断牛/熊/危机
- 多因子评分 (QuantMuse): 动量/质量/波动性因子
- 动态参数调整: 根据市场状态自适应止盈止损
- 改进风控: 回撤控制 + VaR 估算
- TWAP 订单算法 (NexusTrader): 减少市场冲击
"""
import ccxt
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta

class HFTraderV4_5:
    def __init__(self):
        self.exchange = ccxt.okx({
            'apiKey': 'b71ee824-5524-4cde-b818-b8e294c27d56',
            'secret': '76122A8879980469F474F042135584DB',
            'password': 'Qian159.',
            'testnet': True
        })
        
        self.symbol = 'ETH/USDT'
        self.initial_capital = 6769.72
        
        # 基础参数 (会根据市场状态动态调整)
        self.base_position_pct = 0.15
        self.base_stop_loss_pct = 0.01
        self.base_take_profit_pct = 0.02
        
        # 当前参数 (动态调整)
        self.position_pct = self.base_position_pct
        self.stop_loss_pct = self.base_stop_loss_pct
        self.take_profit_pct = self.base_take_profit_pct
        
        # 市场状态
        self.market_state = 'NORMAL'  # BULL/BEAR/CRISIS/NORMAL
        self.vix_level = 0  # 波动率指数
        
        # 多因子评分
        self.factor_scores = {
            'momentum': 0,
            'quality': 0,
            'volatility': 0
        }
        
        # 状态
        self.position = None
        self.entry_price = 0
        self.trades = []
        self.peak_capital = self.initial_capital
        self.max_drawdown = 0
        self.daily_pnl = 0
        
    def get_balance(self):
        b = self.exchange.fetch_balance()
        return b['total'].get('USDT', 0), b['total'].get('ETH', 0)
    
    def get_price(self):
        return self.exchange.fetch_ticker(self.symbol)['last']
    
    def get_historical_data(self, timeframe='1h', limit=100):
        """获取历史数据用于计算 VIX 和因子"""
        ohlcv = self.exchange.fetch_ohlcv(self.symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['t','o','h','l','c','v'])
        return df
    
    def calculate_vix(self):
        """计算波动率指数 (简化版 VIX)"""
        df = self.get_historical_data('1h', limit=50)
        returns = df['c'].pct_change().dropna()
        vix = returns.std() * np.sqrt(252) * 100  # 年化波动率
        return vix
    
    def detect_market_state(self):
        """
        市场状态检测 (来自 AgentQuant)
        使用 VIX + 动量判断牛/熊/危机状态
        """
        vix = self.calculate_vix()
        self.vix_level = vix
        
        # 获取价格动量
        df = self.get_historical_data('4h', limit=50)
        momentum_20 = (df['c'].iloc[-1] - df['c'].iloc[-20]) / df['c'].iloc[-20]
        
        # 状态判断逻辑
        if vix > 80:  # 极高波动率
            self.market_state = 'CRISIS'
        elif vix > 50 and momentum_20 < -0.05:  # 高波动 + 下跌
            self.market_state = 'BEAR'
        elif vix < 30 and momentum_20 > 0.05:  # 低波动 + 上涨
            self.market_state = 'BULL'
        else:
            self.market_state = 'NORMAL'
        
        # 根据市场状态动态调整参数
        self.adjust_parameters()
        
        return self.market_state
    
    def adjust_parameters(self):
        """根据市场状态自适应调整交易参数"""
        if self.market_state == 'CRISIS':
            # 危机模式：极低仓位，极紧止损
            self.position_pct = 0.05
            self.stop_loss_pct = 0.005
            self.take_profit_pct = 0.015
        elif self.market_state == 'BEAR':
            # 熊市：低仓位，紧止损，只做空
            self.position_pct = 0.08
            self.stop_loss_pct = 0.008
            self.take_profit_pct = 0.018
        elif self.market_state == 'BULL':
            # 牛市：高仓位，宽松止损
            self.position_pct = 0.20
            self.stop_loss_pct = 0.015
            self.take_profit_pct = 0.03
        else:  # NORMAL
            # 正常市场：标准参数
            self.position_pct = self.base_position_pct
            self.stop_loss_pct = self.base_stop_loss_pct
            self.take_profit_pct = self.base_take_profit_pct
    
    def calculate_factor_scores(self):
        """
        多因子评分 (来自 QuantMuse)
        动量/质量/波动性因子
        """
        df = self.get_historical_data('1h', limit=100)
        
        # 1. 动量因子 (Momentum)
        mom_10 = df['c'].pct_change(10).iloc[-1]
        mom_20 = df['c'].pct_change(20).iloc[-1]
        self.factor_scores['momentum'] = (mom_10 + mom_20) / 2
        
        # 2. 质量因子 (Quality) - 用夏普比率近似
        returns = df['c'].pct_change().dropna()
        if returns.std() > 0:
            sharpe = (returns.mean() / returns.std()) * np.sqrt(252)
            self.factor_scores['quality'] = sharpe
        else:
            self.factor_scores['quality'] = 0
        
        # 3. 波动性因子 (Volatility) - 低波动得分高
        volatility = returns.std()
        self.factor_scores['volatility'] = -volatility  # 负相关
        
        # 综合评分
        total_score = (
            self.factor_scores['momentum'] * 0.4 +
            self.factor_scores['quality'] * 0.4 +
            self.factor_scores['volatility'] * 0.2
        )
        
        return total_score
    
    def get_multi_tf_data(self):
        """多时间框架分析"""
        data = {}
        for tf, limit in [('1m', 60), ('5m', 50), ('15m', 30)]:
            ohlcv = self.exchange.fetch_ohlcv(self.symbol, tf, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['t','o','h','l','c','v'])
            data[tf] = df
        return data
    
    def calculate_indicators(self, df):
        """计算技术指标"""
        # RSI
        delta = df['c'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        df['rsi'] = 100 - (100 / (1 + gain / loss))
        
        # MACD
        ema12 = df['c'].ewm(span=12).mean()
        ema26 = df['c'].ewm(span=26).mean()
        df['macd'] = ema12 - ema26
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # MA
        df['ma5'] = df['c'].rolling(5).mean()
        df['ma20'] = df['c'].rolling(20).mean()
        
        # ATR
        high_low = df['h'] - df['l']
        high_close = abs(df['h'] - df['c'].shift())
        low_close = abs(df['l'] - df['c'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr'] = tr.rolling(14).mean()
        
        return df
    
    def get_signal(self, data):
        """
        多时间框架信号确认 + 多因子过滤
        只有综合评分高时才交易
        """
        # 先检查多因子评分
        factor_score = self.calculate_factor_scores()
        
        # 如果综合评分太低，不交易
        if abs(factor_score) < 0.01:
            return 'NEUTRAL'
        
        signals = {}
        
        for tf, df in data.items():
            df = self.calculate_indicators(df)
            latest = df.iloc[-1]
            
            # 短期趋势
            if latest['ma5'] > latest['ma20'] and latest['macd_hist'] > 0:
                signals[tf] = 'bullish'
            elif latest['ma5'] < latest['ma20'] and latest['macd_hist'] < 0:
                signals[tf] = 'bearish'
            else:
                signals[tf] = 'neutral'
        
        # 整体信号 (多周期确认)
        bullish_count = sum(1 for v in signals.values() if v == 'bullish')
        bearish_count = sum(1 for v in signals.values() if v == 'bearish')
        
        # 根据市场状态调整信号
        if self.market_state == 'BEAR':
            # 熊市只做空
            if bearish_count >= 2 and factor_score < 0:
                return 'SHORT'
            return 'NEUTRAL'
        elif self.market_state == 'BULL':
            # 牛市只做多
            if bullish_count >= 2 and factor_score > 0:
                return 'LONG'
            return 'NEUTRAL'
        elif self.market_state == 'CRISIS':
            # 危机模式不交易
            return 'NEUTRAL'
        else:
            # 正常市场
            if bullish_count >= 2 and factor_score > 0:
                return 'LONG'
            elif bearish_count >= 2 and factor_score < 0:
                return 'SHORT'
            return 'NEUTRAL'
    
    def calculate_var(self, confidence=0.95):
        """计算 VaR (Value at Risk)"""
        df = self.get_historical_data('1h', limit=100)
        returns = df['c'].pct_change().dropna()
        var = returns.quantile(1 - confidence)
        return abs(var)
    
    def check_risk_limits(self):
        """风控检查 - 回撤和 VaR 限制"""
        usdt, eth = self.get_balance()
        current_capital = usdt + eth * self.get_price()
        
        # 计算当前回撤
        if current_capital > self.peak_capital:
            self.peak_capital = current_capital
        
        drawdown = (self.peak_capital - current_capital) / self.peak_capital
        self.max_drawdown = max(self.max_drawdown, drawdown)
        
        # 计算 VaR
        var = self.calculate_var()
        
        # 风控规则
        if drawdown > 0.10:  # 回撤超过 10%
            return False, f"MAX_DRAWDOWN ({drawdown*100:.1f}%)"
        
        if var > 0.05:  # VaR 超过 5%
            return False, f"HIGH_VaR ({var*100:.1f}%)"
        
        return True, "OK"
    
    def should_exit(self):
        """智能退出判断"""
        if not self.position:
            return False, None
        
        current = self.get_price()
        
        if self.position == 'LONG':
            pnl_pct = (current - self.entry_price) / self.entry_price
        else:
            pnl_pct = (self.entry_price - current) / self.entry_price
        
        # 止盈
        if pnl_pct >= self.take_profit_pct:
            return True, f'TP ({pnl_pct*100:+.1f}%)'
        # 止损
        if pnl_pct <= -self.stop_loss_pct:
            return True, f'SL ({pnl_pct*100:+.1f}%)'
        
        # 反向信号
        data = self.get_multi_tf_data()
        signal = self.get_signal(data)
        if signal == 'SHORT' and self.position == 'LONG':
            return True, f'REVERSE ({pnl_pct*100:+.1f}%)'
        if signal == 'LONG' and self.position == 'SHORT':
            return True, f'REVERSE ({pnl_pct*100:+.1f}%)'
        
        # 市场状态突变
        old_state = self.market_state
        self.detect_market_state()
        if old_state != self.market_state and self.market_state == 'CRISIS':
            return True, f'CRISIS_EXIT ({pnl_pct*100:+.1f}%)'
        
        return False, None
    
    def twap_order(self, side, total_amount, num_slices=5, interval=2):
        """
        TWAP 订单算法 (来自 NexusTrader)
        减少市场冲击
        """
        slice_size = total_amount / num_slices
        filled = 0
        
        for i in range(num_slices):
            try:
                if side == 'BUY':
                    self.exchange.create_market_buy_order(self.symbol, slice_size)
                else:
                    self.exchange.create_market_sell_order(self.symbol, slice_size)
                
                filled += slice_size
                
                if i < num_slices - 1:
                    time.sleep(interval)
                    
            except Exception as e:
                print(f'TWAP slice error: {e}')
                break
        
        return filled
    
    def open_position(self, side):
        """开仓 (使用 TWAP 算法)"""
        usdt, eth = self.get_balance()
        if usdt < 10:
            return False
        
        # 风控检查
        risk_ok, risk_reason = self.check_risk_limits()
        if not risk_ok:
            print(f'Risk limit hit: {risk_reason}')
            return False
        
        amount = (usdt * self.position_pct) / self.get_price()
        amount = round(amount, 4)
        
        try:
            # 使用 TWAP 算法执行订单 (减少市场冲击)
            if side == 'LONG':
                self.twap_order('BUY', amount, num_slices=3, interval=1)
            else:
                self.twap_order('SELL', amount, num_slices=3, interval=1)
            
            self.position = side
            self.entry_price = self.get_price()
            
            print(f'[{datetime.now().strftime("%H:%M:%S")}] {side} OPEN: {amount} @ ${self.entry_price:.2} | State:{self.market_state} | SL:{self.stop_loss_pct*100:.1f}% TP:{self.take_profit_pct*100:.1f}%')
            return True
        except Exception as e:
            print(f'Open error: {e}')
            return False
    
    def close_position(self, reason):
        """平仓"""
        usdt, eth = self.get_balance()
        if eth < 0.001:
            self.position = None
            return
        
        try:
            if self.position == 'LONG':
                self.exchange.create_market_sell_order(self.symbol, eth)
            else:
                self.exchange.create_market_buy_order(self.symbol, eth)
            
            exit_price = self.get_price()
            pnl = (exit_price - self.entry_price) * eth if self.position == 'LONG' else (self.entry_price - exit_price) * eth
            
            print(f'[{datetime.now().strftime("%H:%M:%S")}] {self.position} CLOSE: {reason} @ ${exit_price:.2}, PnL: ${pnl:.2}')
            
            self.trades.append({'entry': self.entry_price, 'exit': exit_price, 'pnl': pnl, 'time': datetime.now()})
            self.position = None
            self.entry_price = 0
        except Exception as e:
            print(f'Close error: {e}')
    
    def print_status(self, iteration, signal, price, total, pnl):
        """打印详细状态"""
        pos_info = ''
        if self.position:
            current_pnl = (price - self.entry_price) / self.entry_price * 100 if self.position == 'LONG' else (self.entry_price - price) / self.entry_price * 100
            pos_info = f' | {self.position} @ ${self.entry_price:.0} ({current_pnl:+.1f}%)'
        
        factor_info = f"M:{self.factor_scores['momentum']:+.3f} Q:{self.factor_scores['quality']:+.3f} V:{self.factor_scores['volatility']:+.3f}"
        
        print(f'[{iteration}] {signal:6} | ${price:.0} | Total:${total:.0} | PnL:${pnl:.0}{pos_info}')
        print(f'       State:{self.market_state:6} VIX:{self.vix_level:.1f} | Factors: {factor_info}')
    
    def run(self, iterations=100, interval=12):
        print('='*80)
        print('HF Trader V4.5 - Enhanced Multi-Factor System')
        print(f'Interval: {interval}s, Iterations: {iterations}')
        print('Features: Market State Detection + Multi-Factor + TWAP + Dynamic Risk')
        print('='*80)
        
        usdt, eth = self.get_balance()
        print(f'Initial Capital: ${usdt:.2}')
        print(f'Market State: {self.detect_market_state()}')
        print('='*80)
        
        for i in range(iterations):
            try:
                # 检测市场状态 (每 10 次迭代更新一次)
                if i % 10 == 0:
                    self.detect_market_state()
                
                # 检查平仓
                should_exit, reason = self.should_exit()
                if should_exit:
                    self.close_position(reason)
                
                # 获取信号
                data = self.get_multi_tf_data()
                signal = self.get_signal(data)
                
                # 开仓
                if not self.position and signal != 'NEUTRAL':
                    self.open_position(signal)
                
                # 状态
                usdt, eth = self.get_balance()
                price = self.get_price()
                total = usdt + eth * price
                pnl = total - self.initial_capital
                
                # 打印状态 (每 5 次迭代打印一次详细信息)
                if i % 5 == 0:
                    self.print_status(i+1, signal, price, total, pnl)
                else:
                    pos_info = ''
                    if self.position:
                        current_pnl = (price - self.entry_price) / self.entry_price * 100 if self.position == 'LONG' else (self.entry_price - price) / self.entry_price * 100
                        pos_info = f' | {self.position} @ ${self.entry_price:.0} ({current_pnl:+.1f}%)'
                    print(f'[{i+1}] {signal:6} | ${price:.0} | Total:${total:.0} | PnL:${pnl:.0}{pos_info}')
                
                time.sleep(interval)
                
            except Exception as e:
                print(f'Error: {e}')
                time.sleep(5)
        
        # Final Report
        usdt, eth = self.get_balance()
        total = usdt + eth * self.get_price()
        final_pnl = total - self.initial_capital
        pnl_pct = ((total / self.initial_capital) - 1) * 100
        
        print('='*80)
        print('FINAL REPORT')
        print('='*80)
        print(f'Final Capital: ${total:.2}')
        print(f'Total PnL: ${final_pnl:.2} ({pnl_pct:.1f}%)')
        print(f'Max Drawdown: {self.max_drawdown*100:.1f}%')
        print(f'Total Trades: {len(self.trades)}')
        
        if len(self.trades) > 0:
            win_trades = [t for t in self.trades if t['pnl'] > 0]
            win_rate = len(win_trades) / len(self.trades) * 100
            avg_pnl = sum(t['pnl'] for t in self.trades) / len(self.trades)
            print(f'Win Rate: {win_rate:.1f}%')
            print(f'Avg PnL/Trade: ${avg_pnl:.2}')
        
        print('='*80)


if __name__ == '__main__':
    trader = HFTraderV4_5()
    trader.run(iterations=100, interval=12)
