#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million Backtester v1.0
回测引擎 - 验证策略在历史数据上的表现
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import json
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import random

class BacktestResult:
    """回测结果"""
    def __init__(self):
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_pnl = 0.0
        self.max_drawdown = 0.0
        self.sharpe_ratio = 0.0
        self.win_rate = 0.0
        self.avg_win = 0.0
        self.avg_loss = 0.0
        self.profit_factor = 0.0
        self.trades = []
        
    def to_dict(self) -> dict:
        return {
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'total_pnl': round(self.total_pnl, 2),
            'max_drawdown': round(self.max_drawdown, 2),
            'win_rate': round(self.win_rate, 2),
            'avg_win': round(self.avg_win, 2),
            'avg_loss': round(self.avg_loss, 2),
            'profit_factor': round(self.profit_factor, 2),
            'trades': self.trades
        }


class Backtester:
    """回测引擎"""
    
    def __init__(self, initial_balance: float = 1000.0):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.leverage = 20
        self.stop_loss_pct = 0.05 / self.leverage  # 5% 账户风险
        self.take_profit_pct = 0.15 / self.leverage  # 15% 账户风险
        self.position_pct = 0.02  # 2% 仓位
        self.max_position = 30
        
        # 策略参数 (v7.2)
        self.rsi_long = 32
        self.rsi_short = 68
        self.rsi_period = 14
        self.ma_short = 5
        self.ma_long = 20
        
    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
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
    
    def calculate_ma(self, prices: List[float], period: int) -> float:
        """计算移动平均"""
        if len(prices) < period:
            return prices[-1] if prices else 0
        return sum(prices[-period:]) / period
    
    def generate_ohlcv(self, days: int = 30, candles_per_day: int = 288) -> List[dict]:
        """生成模拟 OHLCV 数据 (5 分钟 K 线)"""
        candles = []
        base_price = 95000.0  # BTC 起始价格
        
        # 生成带趋势的随机游走
        trend = random.gauss(0.0001, 0.0005)  # 微小趋势
        volatility = 0.002  # 0.2% 波动率
        
        current_price = base_price
        total_candles = days * candles_per_day
        
        for i in range(total_candles):
            # 生成 OHLC
            open_price = current_price
            
            # 随机波动 + 趋势
            change = random.gauss(trend, volatility)
            close_price = open_price * (1 + change)
            
            # 生成高低点
            high_price = max(open_price, close_price) * (1 + abs(random.gauss(0, volatility * 0.5)))
            low_price = min(open_price, close_price) * (1 - abs(random.gauss(0, volatility * 0.5)))
            
            # 成交量
            volume = random.uniform(100, 1000)
            
            candles.append({
                'timestamp': datetime.now() - timedelta(minutes=(total_candles - i) * 5),
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': volume
            })
            
            current_price = close_price
        
        return candles
    
    def check_signal(self, prices: List[float]) -> str:
        """检查交易信号"""
        if len(prices) < self.ma_long:
            return 'HOLD'
        
        rsi = self.calculate_rsi(prices, self.rsi_period)
        ma5 = self.calculate_ma(prices, self.ma_short)
        ma20 = self.calculate_ma(prices, self.ma_long)
        
        # v7.2 信号逻辑
        if rsi <= self.rsi_long and ma5 > ma20:
            return 'LONG'
        elif rsi >= self.rsi_short and ma5 < ma20:
            return 'SHORT'
        
        return 'HOLD'
    
    def run(self, candles: List[dict], symbol: str = 'BTC') -> BacktestResult:
        """运行回测"""
        result = BacktestResult()
        self.balance = self.initial_balance
        
        position = None
        prices = []
        peak_balance = self.initial_balance
        
        print(f"\n{'='*60}")
        print(f"回测开始 - {symbol}")
        print(f"{'='*60}")
        print(f"初始余额：${self.initial_balance:.2f}")
        print(f"杠杆：{self.leverage}x")
        print(f"K 线数量：{len(candles)}")
        print(f"止损：{self.stop_loss_pct*100/self.leverage:.2f}% (价格)")
        print(f"止盈：{self.take_profit_pct*100/self.leverage:.2f}% (价格)")
        print(f"{'='*60}\n")
        
        for i, candle in enumerate(candles):
            prices.append(candle['close'])
            
            # 检查持仓
            if position:
                entry = position['entry_price']
                side = position['side']
                current_price = candle['close']
                
                # 计算盈亏
                if side == 'LONG':
                    pnl_pct = (current_price - entry) / entry
                else:
                    pnl_pct = (entry - current_price) / entry
                
                pnl_usdt = pnl_pct * position['size'] * self.leverage
                
                # 检查止损止盈
                if pnl_pct <= -self.stop_loss_pct:
                    # 止损平仓
                    self.balance += pnl_usdt
                    result.losing_trades += 1
                    result.trades.append({
                        'type': 'CLOSE',
                        'index': i,
                        'side': side,
                        'entry': entry,
                        'exit': current_price,
                        'pnl': pnl_usdt,
                        'reason': 'STOP_LOSS'
                    })
                    position = None
                    
                elif pnl_pct >= self.take_profit_pct:
                    # 止盈平仓
                    self.balance += pnl_usdt
                    result.winning_trades += 1
                    result.trades.append({
                        'type': 'CLOSE',
                        'index': i,
                        'side': side,
                        'entry': entry,
                        'exit': current_price,
                        'pnl': pnl_usdt,
                        'reason': 'TAKE_PROFIT'
                    })
                    position = None
                
                # 更新峰值和最大回撤
                if self.balance > peak_balance:
                    peak_balance = self.balance
                
                drawdown = (peak_balance - self.balance) / peak_balance
                if drawdown > result.max_drawdown:
                    result.max_drawdown = drawdown
            
            # 检查开仓信号
            if not position and len(prices) >= self.ma_long:
                signal = self.check_signal(prices)
                
                if signal in ['LONG', 'SHORT']:
                    position_size = min(self.balance * self.position_pct, self.max_position)
                    position = {
                        'symbol': symbol,
                        'side': signal,
                        'entry_price': candle['close'],
                        'size': position_size,
                        'index': i
                    }
                    result.total_trades += 1
                    
                    result.trades.append({
                        'type': 'OPEN',
                        'index': i,
                        'side': signal,
                        'price': candle['close'],
                        'size': position_size
                    })
        
        # 计算最终统计
        result.total_pnl = self.balance - self.initial_balance
        
        if result.total_trades > 0:
            result.win_rate = result.winning_trades / result.total_trades * 100
            
            # 计算平均盈亏
            wins = [t['pnl'] for t in result.trades if t.get('type') == 'CLOSE' and t['pnl'] > 0]
            losses = [t['pnl'] for t in result.trades if t.get('type') == 'CLOSE' and t['pnl'] < 0]
            
            result.avg_win = sum(wins) / len(wins) if wins else 0
            result.avg_loss = sum(losses) / len(losses) if losses else 0
            
            # 盈亏比
            if result.avg_loss != 0:
                result.profit_factor = abs(result.avg_win / result.avg_loss)
        
        return result
    
    def print_result(self, result: BacktestResult):
        """打印回测结果"""
        print(f"\n{'='*60}")
        print("回测结果总结")
        print(f"{'='*60}")
        print(f"总交易数：{result.total_trades}")
        print(f"盈利交易：{result.winning_trades} ({result.win_rate:.1f}%)")
        print(f"亏损交易：{result.losing_trades}")
        print(f"总盈亏：${result.total_pnl:.2f}")
        print(f"收益率：{(result.total_pnl/self.initial_balance)*100:.2f}%")
        print(f"最大回撤：{result.max_drawdown*100:.2f}%")
        print(f"平均盈利：${result.avg_win:.2f}")
        print(f"平均亏损：${result.avg_loss:.2f}")
        print(f"盈亏比：{result.profit_factor:.2f}")
        print(f"{'='*60}")


def main():
    """主函数"""
    print("="*60)
    print("Web3Million Backtester v1.0")
    print("="*60)
    
    # 创建回测引擎
    backtester = Backtester(initial_balance=670.0)
    
    # 生成模拟数据
    print("\n生成模拟 K 线数据...")
    candles = backtester.generate_ohlcv(days=30, candles_per_day=288)  # 30 天 5 分钟 K 线
    print(f"生成 {len(candles)} 根 K 线")
    
    # 运行回测
    result = backtester.run(candles, symbol='BTC')
    
    # 打印结果
    backtester.print_result(result)
    
    # 保存结果
    summary = result.to_dict()
    summary['config'] = {
        'initial_balance': backtester.initial_balance,
        'leverage': backtester.leverage,
        'rsi_long': backtester.rsi_long,
        'rsi_short': backtester.rsi_short,
        'stop_loss_pct': backtester.stop_loss_pct * backtester.leverage * 100,
        'take_profit_pct': backtester.take_profit_pct * backtester.leverage * 100
    }
    summary['timestamp'] = datetime.now().isoformat()
    
    with open('backtest_result.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n结果已保存至 backtest_result.json")


if __name__ == '__main__':
    main()
