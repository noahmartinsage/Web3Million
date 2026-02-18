#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🦊 妲己量化交易策略引擎 v0.1
自主开发的加密货币交易策略框架
"""

import json
from datetime import datetime
from typing import Dict, List, Optional

class Position:
    """仓位管理"""
    def __init__(self, symbol: str, entry_price: float, amount: float, side: str = 'long'):
        self.symbol = symbol
        self.entry_price = entry_price
        self.amount = amount
        self.side = side
        self.created_at = datetime.now()
    
    def unrealized_pnl(self, current_price: float) -> float:
        """计算未实现盈亏"""
        if self.side == 'long':
            return (current_price - self.entry_price) * self.amount
        else:
            return (self.entry_price - current_price) * self.amount
    
    def pnl_percentage(self, current_price: float) -> float:
        """计算盈亏百分比"""
        if self.side == 'long':
            return ((current_price - self.entry_price) / self.entry_price) * 100
        else:
            return ((self.entry_price - current_price) / self.entry_price) * 100

class GridTradingStrategy:
    """网格交易策略"""
    def __init__(self, symbol: str, base_price: float, grid_levels: int, 
                 grid_spacing: float, total_capital: float):
        self.symbol = symbol
        self.base_price = base_price
        self.grid_levels = grid_levels
        self.grid_spacing = grid_spacing  # 网格间距百分比
        self.total_capital = total_capital
        self.positions: List[Position] = []
        self.orders: List[Dict] = []
        
    def generate_grid(self) -> List[Dict]:
        """生成网格订单"""
        grid = []
        capital_per_level = self.total_capital / (self.grid_levels * 2)
        
        # 买单网格（低于基准价）
        for i in range(1, self.grid_levels + 1):
            buy_price = self.base_price * (1 - i * self.grid_spacing / 100)
            grid.append({
                'type': 'buy',
                'price': buy_price,
                'amount': capital_per_level / buy_price,
                'level': i
            })
        
        # 卖单网格（高于基准价）
        for i in range(1, self.grid_levels + 1):
            sell_price = self.base_price * (1 + i * self.grid_spacing / 100)
            grid.append({
                'type': 'sell',
                'price': sell_price,
                'amount': capital_per_level / sell_price,
                'level': i
            })
        
        self.orders = grid
        return grid
    
    def print_grid(self):
        """打印网格配置"""
        print(f"\n{'='*60}")
        print(f"📊 妲己网格交易策略 - {self.symbol}")
        print(f"{'='*60}")
        print(f"基准价格：${self.base_price:,.2f}")
        print(f"网格数量：{self.grid_levels} 级")
        print(f"网格间距：{self.grid_spacing}%")
        print(f"总资金：${self.total_capital:,.2f}")
        print(f"{'='*60}")
        print(f"{'类型':<6} {'价格':>12} {'数量':>15} {'级别':>8}")
        print(f"{'-'*60}")
        
        for order in sorted(self.orders, key=lambda x: x['price']):
            type_icon = "🟢 买入" if order['type'] == 'buy' else "🔴 卖出"
            print(f"{type_icon:<6} ${order['price']:>10,.2f} {order['amount']:>12.6f} {order['level']:>8}级")
        
        print(f"{'='*60}\n")

class RiskManager:
    """风险管理模块"""
    def __init__(self, total_capital: float, max_position_pct: float = 0.2,
                 stop_loss_pct: float = 0.05, take_profit_pct: float = 0.15):
        self.total_capital = total_capital
        self.max_position_pct = max_position_pct  # 单笔最大仓位
        self.stop_loss_pct = stop_loss_pct  # 止损百分比
        self.take_profit_pct = take_profit_pct  # 止盈百分比
    
    def calculate_position_size(self, price: float) -> float:
        """计算建议仓位大小"""
        max_position_value = self.total_capital * self.max_position_pct
        return max_position_value / price
    
    def get_stop_loss_price(self, entry_price: float, side: str = 'long') -> float:
        """计算止损价格"""
        if side == 'long':
            return entry_price * (1 - self.stop_loss_pct)
        else:
            return entry_price * (1 + self.stop_loss_pct)
    
    def get_take_profit_price(self, entry_price: float, side: str = 'long') -> float:
        """计算止盈价格"""
        if side == 'long':
            return entry_price * (1 + self.take_profit_pct)
        else:
            return entry_price * (1 - self.take_profit_pct)
    
    def print_risk_params(self):
        """打印风险参数"""
        print(f"\n{'='*60}")
        print("🛡️ 妲己风险管理参数")
        print(f"{'='*60}")
        print(f"总资金：${self.total_capital:,.2f}")
        print(f"单笔最大仓位：{self.max_position_pct*100}% (${self.total_capital * self.max_position_pct:,.2f})")
        print(f"止损线：-{self.stop_loss_pct*100}%")
        print(f"止盈线：+{self.take_profit_pct*100}%")
        print(f"{'='*60}\n")

def demo():
    """演示策略"""
    print("\n" + "="*60)
    print("🦊 妲己量化交易策略引擎 v0.1")
    print(f"运行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # 示例：ETH 网格交易策略
    eth_price = 2700  # 模拟价格
    grid_strategy = GridTradingStrategy(
        symbol='ETH/USD',
        base_price=eth_price,
        grid_levels=5,
        grid_spacing=2.0,  # 2% 网格间距
        total_capital=10000  # 1 万美元测试资金
    )
    
    grid_strategy.generate_grid()
    grid_strategy.print_grid()
    
    # 风险管理
    risk_mgr = RiskManager(
        total_capital=10000,
        max_position_pct=0.2,
        stop_loss_pct=0.05,
        take_profit_pct=0.15
    )
    risk_mgr.print_risk_params()
    
    # 示例仓位
    position = Position('ETH', eth_price, 3.7, 'long')
    print(f"\n示例仓位：{position.amount} {position.symbol} @ ${position.entry_price:,.2f}")
    
    # 模拟不同价格下的盈亏
    test_prices = [2500, 2600, 2700, 2800, 2900, 3000]
    print(f"\n{'价格':>10} {'盈亏 ($)':>12} {'盈亏 (%)':>10}")
    print("-" * 35)
    for price in test_prices:
        pnl = position.unrealized_pnl(price)
        pnl_pct = position.pnl_percentage(price)
        print(f"${price:>8,.2f} {pnl:>12,.2f} {pnl_pct:>9.2f}%")

if __name__ == '__main__':
    demo()
