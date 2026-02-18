"""
数据分析和监控仪表板
实时跟踪交易表现和系统状态
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import sqlite3
from dataclasses import dataclass
from enum import Enum


class TradeType(Enum):
    ARBITRAGE = "arbitrage"
    SWAP = "swap"
    LIQUIDITY = "liquidity"
    YIELD_FARMING = "yield_farming"


@dataclass
class TradeRecord:
    timestamp: datetime
    type: TradeType
    pair: str
    amount: float
    entry_price: float
    exit_price: float
    profit: float
    fees: float
    pnl_percent: float
    strategy: str


class AnalyticsEngine:
    def __init__(self, db_path: str = "trading_data.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._setup_database()
        
    def _setup_database(self):
        """初始化数据库表"""
        cursor = self.conn.cursor()
        
        # 交易记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                type TEXT NOT NULL,
                pair TEXT NOT NULL,
                amount REAL NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL,
                profit REAL,
                fees REAL DEFAULT 0,
                pnl_percent REAL,
                strategy TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 资产变动表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS balance_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                asset_type TEXT NOT NULL,
                amount REAL NOT NULL,
                usd_value REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
    
    def record_trade(self, trade: TradeRecord):
        """记录交易"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO trades 
            (timestamp, type, pair, amount, entry_price, exit_price, profit, fees, pnl_percent, strategy)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            trade.timestamp.isoformat(),
            trade.type.value,
            trade.pair,
            trade.amount,
            trade.entry_price,
            trade.exit_price,
            trade.profit,
            trade.fees,
            trade.pnl_percent,
            trade.strategy
        ))
        self.conn.commit()
    
    def record_balance(self, asset_type: str, amount: float, usd_value: float):
        """记录资产变动"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO balance_history (timestamp, asset_type, amount, usd_value)
            VALUES (?, ?, ?, ?)
        ''', (datetime.now().isoformat(), asset_type, amount, usd_value))
        self.conn.commit()
    
    def get_performance_metrics(self, days: int = 30) -> Dict:
        """获取性能指标"""
        cursor = self.conn.cursor()
        
        # 获取指定天数内的交易数据
        since_date = (datetime.now() - timedelta(days=days)).isoformat()
        cursor.execute('''
            SELECT * FROM trades 
            WHERE timestamp >= ? AND profit IS NOT NULL
            ORDER BY timestamp DESC
        ''', (since_date,))
        
        rows = cursor.fetchall()
        if not rows:
            return {}
        
        df = pd.DataFrame(rows, columns=['id', 'timestamp', 'type', 'pair', 'amount', 
                                        'entry_price', 'exit_price', 'profit', 'fees', 'pnl_percent', 'strategy'])
        
        # 计算各项指标
        total_trades = len(df)
        profitable_trades = len(df[df['profit'] > 0])
        win_rate = profitable_trades / total_trades if total_trades > 0 else 0
        total_profit = df['profit'].sum()
        avg_profit = df['profit'].mean() if total_trades > 0 else 0
        profit_std = df['profit'].std() if total_trades > 1 else 0
        sharpe_ratio = (avg_profit / profit_std) * np.sqrt(252) if profit_std != 0 else 0
        
        # 最大连续亏损
        consecutive_losses = 0
        max_consecutive_losses = 0
        for profit in df['profit']:
            if profit <= 0:
                consecutive_losses += 1
                max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
            else:
                consecutive_losses = 0
        
        # 按策略分类统计
        strategy_stats = df.groupby('strategy').agg({
            'profit': ['count', 'sum', 'mean'],
            'pnl_percent': 'mean'
        }).round(4)
        
        return {
            'period_days': days,
            'total_trades': int(total_trades),
            'profitable_trades': int(profitable_trades),
            'win_rate': round(win_rate, 4),
            'total_profit': round(float(total_profit), 4),
            'avg_profit': round(float(avg_profit), 4),
            'sharpe_ratio': round(sharpe_ratio, 4),
            'max_consecutive_losses': int(max_consecutive_losses),
            'volatility': round(float(profit_std), 4),
            'strategy_breakdown': strategy_stats.to_dict() if not strategy_stats.empty else {}
        }
    
    def get_real_time_dashboard(self) -> Dict:
        """获取实时仪表板数据"""
        cursor = self.conn.cursor()
        
        # 当日数据
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        
        cursor.execute('SELECT COUNT(*), SUM(profit) FROM trades WHERE timestamp >= ?', (today_start,))
        today_count, today_profit = cursor.fetchone()
        today_count = today_count or 0
        today_profit = today_profit or 0.0
        
        # 最近24小时数据
        last_24h_start = (datetime.now() - timedelta(hours=24)).isoformat()
        cursor.execute('SELECT COUNT(*), SUM(profit) FROM trades WHERE timestamp >= ?', (last_24h_start,))
        h24_count, h24_profit = cursor.fetchone()
        h24_count = h24_count or 0
        h24_profit = h24_profit or 0.0
        
        # 获取最近的资产历史
        cursor.execute('SELECT timestamp, usd_value FROM balance_history ORDER BY timestamp DESC LIMIT 50')
        balance_data = cursor.fetchall()
        
        # 计算总资产变化趋势
        if balance_data:
            latest_balance = balance_data[0][1]
            if len(balance_data) > 1:
                prev_balance = balance_data[-1][1]
                balance_change = ((latest_balance - prev_balance) / prev_balance) * 100
            else:
                balance_change = 0.0
        else:
            latest_balance = 0.0
            balance_change = 0.0
        
        return {
            'timestamp': datetime.now().isoformat(),
            'today': {
                'trades': int(today_count),
                'profit': round(float(today_profit), 4)
            },
            'last_24h': {
                'trades': int(h24_count),
                'profit': round(float(h24_profit), 4)
            },
            'balance': {
                'current': round(latest_balance, 4),
                'change_pct': round(balance_change, 4)
            },
            'active_strategies': self._get_active_strategies()
        }
    
    def _get_active_strategies(self) -> List[str]:
        """获取活跃策略列表"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT DISTINCT strategy FROM trades WHERE timestamp >= ?', 
                      ((datetime.now() - timedelta(days=7)).isoformat(),))
        strategies = [row[0] for row in cursor.fetchall() if row[0]]
        return strategies
    
    def generate_performance_chart(self, days: int = 30) -> str:
        """生成性能图表"""
        cursor = self.conn.cursor()
        
        # 获取数据
        since_date = (datetime.now() - timedelta(days=days)).isoformat()
        cursor.execute('''
            SELECT timestamp, profit FROM trades 
            WHERE timestamp >= ? AND profit IS NOT NULL
            ORDER BY timestamp
        ''', (since_date,))
        
        rows = cursor.fetchall()
        if not rows:
            return "No data available"
        
        df = pd.DataFrame(rows, columns=['timestamp', 'profit'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')
        
        # 计算累积收益
        df['cumulative_profit'] = df['profit'].cumsum()
        df['balance'] = 10.0 + df['cumulative_profit']  # 假设初始资金10美元
        
        # 创建图表
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('累积收益', '每日盈亏'),
            vertical_spacing=0.1
        )
        
        # 累积收益曲线
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['balance'],
                mode='lines',
                name='账户余额',
                line=dict(color='blue', width=2)
            ),
            row=1, col=1
        )
        
        # 每日盈亏柱状图
        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df['profit'],
                name='每日盈亏',
                marker_color=np.where(df['profit'] >= 0, 'green', 'red')
            ),
            row=2, col=1
        )
        
        fig.update_layout(
            title=f'过去{days}天交易表现',
            height=600,
            showlegend=True
        )
        
        fig.update_xaxes(title_text="日期", row=2, col=1)
        fig.update_yaxes(title_text="余额 (USD)", row=1, col=1)
        fig.update_yaxes(title_text="盈亏 (USD)", row=2, col=1)
        
        chart_path = f"performance_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        fig.write_html(chart_path)
        
        return chart_path
    
    def get_strategy_analysis(self) -> Dict:
        """策略分析"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT strategy, 
                   COUNT(*) as total_trades,
                   SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END) as winning_trades,
                   AVG(profit) as avg_profit,
                   SUM(profit) as total_profit,
                   AVG(pnl_percent) as avg_pnl_percent
            FROM trades 
            WHERE strategy IS NOT NULL
            GROUP BY strategy
        ''')
        
        rows = cursor.fetchall()
        if not rows:
            return {}
        
        analysis = {}
        for row in rows:
            strategy, total, winning, avg_profit, total_profit, avg_pnl = row
            win_rate = winning / total if total > 0 else 0
            analysis[strategy] = {
                'total_trades': int(total),
                'winning_trades': int(winning),
                'win_rate': round(win_rate, 4),
                'avg_profit': round(float(avg_profit), 4),
                'total_profit': round(float(total_profit), 4),
                'avg_pnl_percent': round(float(avg_pnl), 4)
            }
        
        return analysis


class AlertSystem:
    """警报系统"""
    def __init__(self, analytics: AnalyticsEngine):
        self.analytics = analytics
        self.alert_thresholds = {
            'max_daily_loss': -10,  # 单日最大亏损10美元
            'max_consecutive_losses': 5,  # 最大连续亏损次数
            'low_win_rate': 0.4,  # 最低胜率
            'high_volatility': 0.05  # 高波动率阈值
        }
    
    def check_alerts(self) -> List[Dict]:
        """检查警报条件"""
        alerts = []
        metrics = self.analytics.get_performance_metrics(days=1)  # 检查当日数据
        
        if not metrics:
            return alerts
        
        # 检查单日亏损
        if metrics.get('total_profit', 0) < self.alert_thresholds['max_daily_loss']:
            alerts.append({
                'type': 'DAILY_LOSS_EXCEEDED',
                'severity': 'HIGH',
                'message': f'单日亏损 ${metrics["total_profit"]} 超过阈值 ${self.alert_thresholds["max_daily_loss"]}',
                'timestamp': datetime.now().isoformat()
            })
        
        # 检查连续亏损
        if metrics.get('max_consecutive_losses', 0) >= self.alert_thresholds['max_consecutive_losses']:
            alerts.append({
                'type': 'CONSECUTIVE_LOSSES',
                'severity': 'MEDIUM',
                'message': f'出现 {metrics["max_consecutive_losses"]} 次连续亏损',
                'timestamp': datetime.now().isoformat()
            })
        
        # 检查胜率
        if metrics.get('win_rate', 1) < self.alert_thresholds['low_win_rate']:
            alerts.append({
                'type': 'LOW_WIN_RATE',
                'severity': 'MEDIUM',
                'message': f'胜率 {metrics["win_rate"]:.2%} 低于阈值 {self.alert_thresholds["low_win_rate"]:.2%}',
                'timestamp': datetime.now().isoformat()
            })
        
        return alerts


# 使用示例
if __name__ == "__main__":
    analytics = AnalyticsEngine()
    
    # 模拟一些交易数据
    for i in range(100):
        trade = TradeRecord(
            timestamp=datetime.now() - timedelta(minutes=i*10),
            type=TradeType.ARBITRAGE,
            pair="ETH/USDT",
            amount=np.random.uniform(0.1, 1.0),
            entry_price=np.random.uniform(2500, 3000),
            exit_price=np.random.uniform(2500, 3000),
            profit=np.random.uniform(-5, 10),
            fees=np.random.uniform(0.1, 0.5),
            pnl_percent=np.random.uniform(-0.02, 0.03),
            strategy="simple_arbitrage"
        )
        analytics.record_trade(trade)
    
    # 获取性能指标
    metrics = analytics.get_performance_metrics()
    print("性能指标:", json.dumps(metrics, indent=2, default=str))
    
    # 获取实时仪表板
    dashboard = analytics.get_real_time_dashboard()
    print("\n实时仪表板:", json.dumps(dashboard, indent=2, default=str))
    
    # 策略分析
    strategy_analysis = analytics.get_strategy_analysis()
    print("\n策略分析:", json.dumps(strategy_analysis, indent=2, default=str))
    
    # 检查警报
    alert_system = AlertSystem(analytics)
    alerts = alert_system.check_alerts()
    print("\n警报:", json.dumps(alerts, indent=2, default=str))