"""
高级风险管理系统
用于保护本金并优化收益
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json


class AdvancedRiskManager:
    def __init__(self, initial_capital: float = 10.0):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.max_drawdown = 0.15  # 最大回撤15%
        self.max_single_loss = 0.05  # 单次最大损失5%
        self.max_position_size = 0.2  # 最大仓位20%
        self.min_win_rate = 0.55  # 最低胜率要求55%
        
        # 交易历史记录
        self.trade_history = []
        self.daily_pnl = {}
        
        # 风险指标
        self.sharpe_ratio = 0
        self.sortino_ratio = 0
        self.max_runup = 0
        
    def update_capital(self, new_capital: float):
        """更新当前资本"""
        self.current_capital = new_capital
        self._check_risk_limits()
        
    def record_trade(self, trade_result: Dict):
        """记录交易结果"""
        self.trade_history.append({
            'timestamp': datetime.now(),
            'result': trade_result,
            'capital_after': self.current_capital
        })
        
        # 更新日收益
        day = datetime.now().date()
        if day not in self.daily_pnl:
            self.daily_pnl[day] = 0
        self.daily_pnl[day] += trade_result.get('profit', 0)
        
    def should_continue_trading(self) -> bool:
        """判断是否应该继续交易"""
        # 检查各种风险限制
        if self._is_beyond_drawdown_limit():
            print("❌ 达到最大回撤限制，暂停交易!")
            return False
            
        if self._has_low_win_rate():
            print("❌ 胜率过低，暂停交易!")
            return False
            
        return True
        
    def calculate_position_size(self, strategy_confidence: float = 1.0) -> float:
        """计算仓位大小"""
        # 基础仓位 = 最大仓位 * 资本 * 策略信心度
        base_size = self.max_position_size * self.current_capital * strategy_confidence
        
        # 应用凯利准则调整
        win_rate = self._calculate_recent_win_rate()
        avg_win = self._calculate_avg_win()
        avg_loss = self._calculate_avg_loss()
        
        if avg_loss != 0:
            kelly_fraction = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
            kelly_size = self.current_capital * max(0, min(kelly_fraction, 0.2))  # 限制在20%
            
            # 取保守估计
            return min(base_size, kelly_size)
        else:
            return base_size * 0.1  # 保守起见，只用10%
    
    def get_risk_adjusted_return(self) -> float:
        """获取风险调整后收益"""
        if len(self.trade_history) < 2:
            return 0
            
        returns = [trade['result'].get('return', 0) for trade in self.trade_history[-30:]]
        if len(returns) < 2:
            return 0
            
        avg_return = np.mean(returns)
        volatility = np.std(returns)
        
        if volatility == 0:
            return avg_return * 252  # 年化收益
            
        self.sharpe_ratio = (avg_return * 252) / (volatility * np.sqrt(252))
        return self.sharpe_ratio
    
    def _check_risk_limits(self):
        """检查风险限制"""
        total_loss = (self.initial_capital - self.current_capital) / self.initial_capital
        if total_loss > self.max_drawdown:
            print(f"🚨 总亏损 {total_loss:.2%} 超过最大回撤限制 {self.max_drawdown:.2%}")
            
    def _is_beyond_drawdown_limit(self) -> bool:
        """检查是否超出回撤限制"""
        total_loss = (self.initial_capital - self.current_capital) / self.initial_capital
        return total_loss > self.max_drawdown
    
    def _has_low_win_rate(self) -> bool:
        """检查胜率是否过低"""
        recent_trades = self.trade_history[-20:]  # 最近20笔交易
        if len(recent_trades) < 5:
            return False
            
        wins = sum(1 for t in recent_trades if t['result'].get('profit', 0) > 0)
        win_rate = wins / len(recent_trades)
        
        return win_rate < self.min_win_rate
    
    def _calculate_recent_win_rate(self) -> float:
        """计算近期胜率"""
        recent_trades = self.trade_history[-30:]
        if not recent_trades:
            return 0.5  # 默认50%
            
        wins = sum(1 for t in recent_trades if t['result'].get('profit', 0) > 0)
        return wins / len(recent_trades)
    
    def _calculate_avg_win(self) -> float:
        """计算平均盈利"""
        wins = [t['result'].get('profit', 0) for t in self.trade_history[-30:] 
                if t['result'].get('profit', 0) > 0]
        return np.mean(wins) if wins else 0
    
    def _calculate_avg_loss(self) -> float:
        """计算平均亏损"""
        losses = [abs(t['result'].get('profit', 0)) for t in self.trade_history[-30:] 
                  if t['result'].get('profit', 0) < 0]
        return np.mean(losses) if losses else 0
    
    def generate_report(self) -> Dict:
        """生成风险报告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'current_capital': self.current_capital,
            'total_return': (self.current_capital - self.initial_capital) / self.initial_capital,
            'sharpe_ratio': self.sharpe_ratio,
            'total_trades': len(self.trade_history),
            'recent_win_rate': self._calculate_recent_win_rate(),
            'max_drawdown_reached': self._is_beyond_drawdown_limit(),
            'recommendation': 'CONTINUE' if self.should_continue_trading() else 'STOP'
        }
        
        return report


class PortfolioOptimizer:
    """投资组合优化器"""
    def __init__(self, risk_manager: AdvancedRiskManager):
        self.risk_manager = risk_manager
        self.strategies = {}  # 策略名称 -> 权重
        
    def add_strategy(self, name: str, expected_return: float, risk_level: float):
        """添加策略"""
        self.strategies[name] = {
            'expected_return': expected_return,
            'risk_level': risk_level,
            'allocation': 0  # 初始分配为0
        }
    
    def optimize_allocation(self) -> Dict[str, float]:
        """优化资产配置"""
        if not self.strategies:
            return {}
            
        # 简化的均值方差优化
        total_expected_return = sum(s['expected_return'] for s in self.strategies.values())
        
        allocations = {}
        for name, strategy in self.strategies.items():
            # 基于期望收益分配权重，同时考虑风险
            weight = strategy['expected_return'] / total_expected_return if total_expected_return != 0 else 0
            # 调整以降低高风险策略的权重
            adjusted_weight = weight * (1 - strategy['risk_level'])
            allocations[name] = max(0, adjusted_weight)
        
        # 归一化权重
        total_weight = sum(allocations.values())
        if total_weight > 0:
            for name in allocations:
                allocations[name] /= total_weight
        
        return allocations


# 使用示例
if __name__ == "__main__":
    risk_mgr = AdvancedRiskManager(initial_capital=10.0)
    
    # 模拟一些交易结果
    for i in range(10):
        trade_result = {
            'profit': np.random.choice([5, -2, 3, -1, 4], p=[0.4, 0.1, 0.3, 0.1, 0.1]),
            'return': np.random.normal(0.01, 0.02)
        }
        risk_mgr.record_trade(trade_result)
        risk_mgr.update_capital(risk_mgr.current_capital + trade_result['profit'])
    
    # 生成报告
    report = risk_mgr.generate_report()
    print(json.dumps(report, indent=2, default=str))