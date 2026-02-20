#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million 阶段 1: 测试网运行
启动 v4.5 高频量化交易系统进行测试网实盘验证
"""
import ccxt
import pandas as pd
import numpy as np
import time
import json
from datetime import datetime

class TestnetPhase1:
    def __init__(self):
        # 连接 OKX 测试网
        self.exchange = ccxt.okx({
            'apiKey': 'b71ee824-5524-4cde-b818-b8e294c27d56',
            'secret': '76122A8879980469F474F042135584DB',
            'password': 'Qian159.',
            'testnet': True
        })
        
        self.symbol = 'ETH/USDT'
        self.initial_capital = 6846.73  # 当前测试网资金
        
        # 风控参数
        self.max_position_pct = 0.15  # 单笔最大仓位 15%
        self.stop_loss_pct = 0.01     # 止损 1%
        self.take_profit_pct = 0.02   # 止盈 2%
        self.max_drawdown = 0.10      # 最大回撤 10%
        
        # 状态跟踪
        self.position = None
        self.entry_price = 0
        self.trades = []
        self.peak_capital = self.initial_capital
        self.current_drawdown = 0
        
        print('=' * 70)
        print('Web3Million - 阶段 1: 测试网运行启动')
        print('=' * 70)
        print(f'启动时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        print(f'初始资金：${self.initial_capital:.2f} USDT')
        print(f'交易对：{self.symbol}')
        print(f'风控参数：仓位{self.max_position_pct*100:.0f}% | 止损{self.stop_loss_pct*100:.1f}% | 止盈{self.take_profit_pct*100:.1f}%')
        print('=' * 70)
    
    def get_balance(self):
        """获取账户余额"""
        balance = self.exchange.fetch_balance()
        usdt = balance['total'].get('USDT', 0)
        eth = balance['total'].get('ETH', 0)
        return usdt, eth
    
    def get_price(self):
        """获取当前价格"""
        ticker = self.exchange.fetch_ticker(self.symbol)
        return ticker['last']
    
    def get_market_data(self, timeframe='15m', limit=100):
        """获取市场数据"""
        ohlcv = self.exchange.fetch_ohlcv(self.symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    
    def calculate_indicators(self, df):
        """计算技术指标"""
        # MACD
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = exp1 - exp2
        df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # 布林带
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        
        # 均线
        df['ma20'] = df['close'].rolling(window=20).mean()
        df['ma50'] = df['close'].rolling(window=50).mean()
        
        return df
    
    def generate_signal(self, df):
        """生成交易信号"""
        last = df.iloc[-1]
        
        # 多因子评分
        score = 0
        
        # MACD 信号
        if last['macd'] > last['signal']:
            score += 1
        else:
            score -= 1
        
        # RSI 信号
        if last['rsi'] < 30:
            score += 2  # 超卖
        elif last['rsi'] > 70:
            score -= 2  # 超买
        elif last['rsi'] < 50:
            score += 1
        else:
            score -= 1
        
        # 均线信号
        if last['close'] > last['ma20'] > last['ma50']:
            score += 2  # 多头排列
        elif last['close'] < last['ma20'] < last['ma50']:
            score -= 2  # 空头排列
        
        # 布林带信号
        if last['close'] < last['bb_lower']:
            score += 1  # 触及下轨
        elif last['close'] > last['bb_upper']:
            score -= 1  # 触及上轨
        
        # 生成信号
        if score >= 3:
            return 'BUY', score
        elif score <= -3:
            return 'SELL', score
        else:
            return 'HOLD', score
    
    def execute_trade(self, side, amount):
        """执行交易"""
        try:
            order = self.exchange.create_order(self.symbol, 'market', side, amount)
            return {
                'success': True,
                'side': side,
                'amount': amount,
                'price': order['average'] if order['average'] else order['price'],
                'timestamp': datetime.now()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def run_monitoring(self, interval=60):
        """运行监控循环"""
        print('\n[系统] 开始监控市场...')
        print(f'刷新间隔：{interval}秒\n')
        
        iteration = 0
        while True:
            iteration += 1
            timestamp = datetime.now().strftime('%H:%M:%S')
            
            try:
                # 获取数据
                price = self.get_price()
                usdt, eth = self.get_balance()
                total_value = usdt + (eth * price)
                
                # 计算盈亏
                pnl = total_value - self.initial_capital
                pnl_pct = (pnl / self.initial_capital) * 100
                
                # 更新峰值和回撤
                if total_value > self.peak_capital:
                    self.peak_capital = total_value
                self.current_drawdown = (self.peak_capital - total_value) / self.peak_capital
                
                # 获取市场数据和信号
                df = self.get_market_data()
                df = self.calculate_indicators(df)
                signal, score = self.generate_signal(df)
                
                # 打印状态
                print(f'[{timestamp}] 价格：${price:.2f} | 资产：${total_value:.2f} | 盈亏：{pnl:+.2f} ({pnl_pct:+.2f}%)')
                print(f'         信号：{signal} (得分：{score}) | 回撤：{self.current_drawdown*100:.2f}%')
                print(f'         持仓：USDT={usdt:.2f} | ETH={eth:.4f}\n')
                
                # 检查风控
                if self.current_drawdown > self.max_drawdown:
                    print('[风控] 触发最大回撤限制，停止交易')
                    break
                
                # 执行交易逻辑
                if signal == 'BUY' and self.position is None:
                    # 买入
                    amount = (usdt * self.max_position_pct) / price
                    if amount > 0.001:  # 最小交易量
                        result = self.execute_trade('buy', amount)
                        if result['success']:
                            self.position = 'LONG'
                            self.entry_price = result['price']
                            self.trades.append(result)
                            print(f'[交易] 买入 {amount:.4f} ETH @ ${result["price"]:.2f}\n')
                
                elif signal == 'SELL' and self.position == 'LONG':
                    # 卖出
                    amount = eth * 0.95  # 卖出 95%
                    if amount > 0.001:
                        result = self.execute_trade('sell', amount)
                        if result['success']:
                            pnl_trade = (result['price'] - self.entry_price) / self.entry_price
                            self.trades[-1]['pnl'] = pnl_trade
                            self.position = None
                            self.entry_price = 0
                            print(f'[交易] 卖出 {amount:.4f} ETH @ ${result["price"]:.2f} | 盈亏：{pnl_trade*100:+.2f}%\n')
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                print('\n[系统] 用户中断，停止运行')
                break
            except Exception as e:
                print(f'[错误] {e}')
                time.sleep(interval)
        
        # 最终报告
        self.print_final_report()
    
    def print_final_report(self):
        """打印最终报告"""
        print('\n' + '=' * 70)
        print('阶段 1: 测试网运行 - 最终报告')
        print('=' * 70)
        
        usdt, eth = self.get_balance()
        price = self.get_price()
        total_value = usdt + (eth * price)
        
        pnl = total_value - self.initial_capital
        pnl_pct = (pnl / self.initial_capital) * 100
        
        print(f'初始资金：${self.initial_capital:.2f}')
        print(f'最终资金：${total_value:.2f}')
        print(f'总盈亏：${pnl:+.2f} ({pnl_pct:+.2f}%)')
        print(f'最大回撤：{self.current_drawdown*100:.2f}%')
        print(f'交易次数：{len(self.trades)}')
        
        if len(self.trades) > 0:
            win_trades = [t for t in self.trades if t.get('pnl', 0) > 0]
            win_rate = len(win_trades) / len(self.trades) * 100
            print(f'胜率：{win_rate:.1f}%')
        
        print('=' * 70)


if __name__ == '__main__':
    system = TestnetPhase1()
    system.run_monitoring(interval=30)  # 30 秒刷新一次
