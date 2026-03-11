#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million 参数优化回测器
扫描不同 RSI 阈值，找到最优参数组合
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import json
import random
from datetime import datetime, timedelta
from typing import List, Dict

class OptimizedBacktester:
    """参数优化回测器"""
    
    def __init__(self, initial_balance: float = 670.0):
        self.initial_balance = initial_balance
        self.leverage = 20
        self.position_pct = 0.02
        self.max_position = 30
        
    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
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
        if len(prices) < period:
            return prices[-1] if prices else 0
        return sum(prices[-period:]) / period
    
    def generate_volatile_data(self, days: int = 30) -> List[float]:
        """生成高波动数据 (更容易触发 RSI 极端值)"""
        prices = [95000.0]
        
        # 创建带周期波动的价格
        for i in range(days * 288):
            # 基础趋势
            trend = math.sin(i / 500) * 0.02  # 周期性趋势
            # 随机波动
            noise = random.gauss(0, 0.003)
            # 偶尔的大幅波动 (模拟真实市场)
            if random.random() < 0.02:  # 2% 概率大幅波动
                noise += random.gauss(0, 0.02)
            
            change = trend + noise
            new_price = prices[-1] * (1 + change)
            prices.append(max(new_price, prices[-1] * 0.9))
        
        return prices
    
    def test_params(self, prices: List[float], rsi_long: int, rsi_short: int) -> Dict:
        """测试一组参数"""
        balance = self.initial_balance
        position = None
        peak_balance = balance
        max_drawdown = 0
        trades = []
        wins = 0
        losses = 0
        
        stop_loss_pct = 0.05 / self.leverage
        take_profit_pct = 0.15 / self.leverage
        
        for i in range(len(prices)):
            price = prices[i]
            
            # 检查持仓
            if position:
                entry = position['entry_price']
                side = position['side']
                
                if side == 'LONG':
                    pnl_pct = (price - entry) / entry
                else:
                    pnl_pct = (entry - price) / entry
                
                pnl_usdt = pnl_pct * position['size'] * self.leverage
                
                # 止损/止盈
                if pnl_pct <= -stop_loss_pct:
                    balance += pnl_usdt
                    losses += 1
                    trades.append({'type': 'LOSS', 'pnl': pnl_usdt})
                    position = None
                elif pnl_pct >= take_profit_pct:
                    balance += pnl_usdt
                    wins += 1
                    trades.append({'type': 'WIN', 'pnl': pnl_usdt})
                    position = None
                
                # 更新回撤
                if balance > peak_balance:
                    peak_balance = balance
                dd = (peak_balance - balance) / peak_balance
                if dd > max_drawdown:
                    max_drawdown = dd
            
            # 检查开仓
            if not position and i >= 20:
                window = prices[max(0,i-50):i+1]
                rsi = self.calculate_rsi(window)
                ma5 = self.calculate_ma(window, 5)
                ma20 = self.calculate_ma(window, 20)
                
                if rsi <= rsi_long and ma5 > ma20:
                    size = min(balance * self.position_pct, self.max_position)
                    position = {'side': 'LONG', 'entry_price': price, 'size': size}
                elif rsi >= rsi_short and ma5 < ma20:
                    size = min(balance * self.position_pct, self.max_position)
                    position = {'side': 'SHORT', 'entry_price': price, 'size': size}
        
        total_pnl = balance - self.initial_balance
        total_trades = wins + losses
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        
        return {
            'rsi_long': rsi_long,
            'rsi_short': rsi_short,
            'total_trades': total_trades,
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'roi': (total_pnl / self.initial_balance * 100),
            'max_drawdown': max_drawdown * 100,
            'final_balance': balance
        }
    
    def optimize(self, days: int = 30) -> List[Dict]:
        """参数优化扫描"""
        import math
        
        print(f"\n{'='*60}")
        print("参数优化回测 - RSI 阈值扫描")
        print(f"{'='*60}")
        
        # 生成数据
        prices = self.generate_volatile_data(days)
        print(f"生成价格数据：{len(prices)} 个点")
        
        # 扫描不同参数组合
        results = []
        print(f"\n扫描参数组合...\n")
        print(f"{'RSI Long':<10} {'RSI Short':<10} {'交易数':<8} {'胜率':<8} {'ROI':<10} {'最大回撤':<10}")
        print(f"{'-'*60}")
        
        for rsi_long in [25, 30, 35, 40]:
            for rsi_short in [60, 65, 70, 75]:
                result = self.test_params(prices, rsi_long, rsi_short)
                results.append(result)
                print(f"{rsi_long:<10} {rsi_short:<10} {result['total_trades']:<8} {result['win_rate']:<8.1f}% {result['roi']:<10.2f}% {result['max_drawdown']:<10.2f}%")
        
        # 找出最优参数
        best_by_roi = max(results, key=lambda x: x['roi'])
        best_by_sharpe = max(results, key=lambda x: x['roi'] / (x['max_drawdown'] + 0.01))
        
        print(f"\n{'='*60}")
        print("最优参数 (按 ROI)")
        print(f"{'='*60}")
        print(f"RSI Long: {best_by_roi['rsi_long']}, RSI Short: {best_by_roi['rsi_short']}")
        print(f"交易数：{best_by_roi['total_trades']}, 胜率：{best_by_roi['win_rate']:.1f}%")
        print(f"ROI: {best_by_roi['roi']:.2f}%, 最大回撤：{best_by_roi['max_drawdown']:.2f}%")
        print(f"最终余额：${best_by_roi['final_balance']:.2f}")
        
        print(f"\n{'='*60}")
        print("最优参数 (按风险调整收益)")
        print(f"{'='*60}")
        print(f"RSI Long: {best_by_sharpe['rsi_long']}, RSI Short: {best_by_sharpe['rsi_short']}")
        print(f"交易数：{best_by_sharpe['total_trades']}, 胜率：{best_by_sharpe['win_rate']:.1f}%")
        print(f"ROI: {best_by_sharpe['roi']:.2f}%, 最大回撤：{best_by_sharpe['max_drawdown']:.2f}%")
        
        # 保存结果
        with open('parameter_optimization.json', 'w', encoding='utf-8') as f:
            json.dump({
                'scan_results': results,
                'best_by_roi': best_by_roi,
                'best_by_sharpe': best_by_sharpe,
                'timestamp': datetime.now().isoformat()
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n结果已保存至 parameter_optimization.json")
        
        return results


def main():
    print("="*60)
    print("Web3Million 参数优化回测器 v1.0")
    print("="*60)
    
    backtester = OptimizedBacktester(initial_balance=670.0)
    backtester.optimize(days=30)


if __name__ == '__main__':
    import math
    main()
