#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million AI自治代理系统 - 高频量化交易核心引擎
支持小额高倍杠杆交易 + 强化学习自我进化
"""
import ccxt
import time
import json
import random
from collections import deque
from datetime import datetime
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class AIAgentTradingSystem:
    """AI自治代理高频交易系统"""
    
    def __init__(self, initial_capital=10, leverage=10):
        # 核心配置
        self.initial_capital = initial_capital  # 小额启动资金
        self.leverage = leverage  # 杠杆倍数 (10-100x)
        self.max_position_pct = 0.05  # 最大仓位5%
        self.max_daily_loss = initial_capital * 0.1  # 日内最大亏损10%
        self.stop_loss_pct = 0.02  # 2%止损
        self.take_profit_pct = 0.06  # 6%止盈 (6%*10x=60%收益)
        
        # 交易所配置 (OKX测试网)
        self.exchange = ccxt.okx({
            'apiKey': 'b71ee824-5524-4cde-b818-b8e294c27d56',
            'secret': '76122A8879980469F474F042135584DB',
            'password': 'Qian159.',
            'testnet': True
        })
        
        # 交易对配置
        self.trading_pairs = [
            'BTC/USDT:USDT',
            'ETH/USDT:USDT', 
            'SOL/USDT:USDT',
            'XRP/USDT:USDT',
            'DOGE/USDT:USDT'
        ]
        
        # 状态管理
        self.current_capital = initial_capital
        self.daily_pnl = 0
        self.total_trades = 0
        self.winning_trades = 0
        self.position = None
        
        # 强化学习经验池
        self.experience_buffer = deque(maxlen=10000)
        self.q_table = {}  # Q学习表
        self.gamma = 0.9  # 折扣因子
        self.learning_rate = 0.1
        self.epsilon = 1.0  # 探索率
        self.epsilon_decay = 0.995
        self.epsilon_min = 0.01
        
        # 高频交易参数
        self.tick_interval = 0.1  # 100ms tick
        self.order_book_depth = 5
        self.spread_threshold = 0.001  # 0.1%价差
        
        # 性能统计
        self.stats = {
            'start_time': datetime.now().isoformat(),
            'trades': [],
            'pnl_history': [],
            'agent_state_visits': {}
        }
        
    def get_market_data(self, symbol):
        """获取高频市场数据"""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            order_book = self.exchange.fetch_order_book(symbol, limit=10)
            
            return {
                'symbol': symbol,
                'price': ticker['last'],
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'spread': (ticker['ask'] - ticker['bid']) / ticker['last'],
                'volume': ticker['quoteVolume'],
                'order_book_bids': order_book['bids'][:5],
                'order_book_asks': order_book['asks'][:5],
                'timestamp': time.time()
            }
        except Exception as e:
            return None
    
    def calculate_position_size(self, price):
        """计算仓位大小 - 小额高倍策略"""
        # 每次只用本金的5%
        position_value = self.current_capital * self.max_position_pct * self.leverage
        quantity = position_value / price
        return quantity
    
    def get_state(self, market_data):
        """将市场数据转换为代理状态"""
        if not market_data:
            return None
            
        price = market_data['price']
        spread = market_data['spread']
        
        # 状态离散化
        price_change_bin = int(price / 100) % 100
        spread_bin = int(spread * 1000)
        volume_bin = int(market_data['volume'] / 10000) % 10
        
        state = f"{price_change_bin}_{spread_bin}_{volume_bin}"
        return state
    
    def choose_action(self, state):
        """Epsilon-Greedy策略选择动作"""
        if random.random() < self.epsilon:
            return random.choice(['buy', 'sell', 'hold'])
        
        # Q学习选择最佳动作
        if state not in self.q_table:
            self.q_table[state] = {'buy': 0, 'sell': 0, 'hold': 0}
        
        return max(self.q_table[state], key=self.q_table[state].get)
    
    def execute_trade(self, symbol, action, quantity, price):
        """执行交易"""
        try:
            if action == 'buy':
                order = self.exchange.create_market_buy_order(symbol, quantity)
            elif action == 'sell':
                order = self.exchange.create_market_sell_order(symbol, quantity)
            else:
                return None
                
            return {
                'symbol': symbol,
                'action': action,
                'quantity': quantity,
                'price': price,
                'order_id': order.get('id'),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return None
    
    def update_q_value(self, state, action, reward, next_state):
        """Q学习更新"""
        if state not in self.q_table:
            self.q_table[state] = {'buy': 0, 'sell': 0, 'hold': 0}
        if next_state not in self.q_table:
            self.q_table[next_state] = {'buy': 0, 'sell': 0, 'hold': 0}
        
        current_q = self.q_table[state][action]
        max_next_q = max(self.q_table[next_state].values())
        
        # Q学习公式
        new_q = current_q + self.learning_rate * (reward + self.gamma * max_next_q - current_q)
        self.q_table[state][action] = new_q
    
    def calculate_reward(self, trade_result, market_data):
        """计算交易奖励"""
        if not trade_result or not market_data:
            return 0
            
        # 简化奖励：基于价格变动和仓位方向
        price_change = market_data['spread'] * 100  # 价差百分比
        
        if trade_result['action'] == 'buy':
            return price_change * self.leverage
        elif trade_result['action'] == 'sell':
            return -price_change * self.leverage
        return 0
    
    def check_risk_limits(self):
        """风险检查"""
        # 日内亏损检查
        if self.daily_pnl <= -self.max_daily_loss:
            return False, "daily_loss_limit"
            
        # 止损检查
        if self.position:
            pnl_pct = (self.current_capital - self.initial_capital) / self.initial_capital
            if pnl_pct <= -self.stop_loss_pct:
                return False, "stop_loss"
                
        return True, None
    
    def high_frequency_scan(self):
        """高频扫描套利机会"""
        opportunities = []
        
        for pair in self.trading_pairs:
            data = self.get_market_data(pair)
            if not data:
                continue
                
            # 价差套利
            if data['spread'] > self.spread_threshold:
                opportunities.append({
                    'type': 'spread',
                    'symbol': pair,
                    'spread': data['spread'],
                    'bid': data['bid'],
                    'ask': data['ask']
                })
                
            # 订单簿套利
            if len(data['order_book_bids']) > 0 and len(data['order_book_asks']) > 0:
                best_bid = data['order_book_bids'][0][0]
                best_ask = data['order_book_asks'][0][0]
                book_spread = (best_ask - best_bid) / best_bid
                
                if book_spread > self.spread_threshold:
                    opportunities.append({
                        'type': 'orderbook',
                        'symbol': pair,
                        'spread': book_spread,
                        'best_bid': best_bid,
                        'best_ask': best_ask
                    })
        
        return opportunities
    
    def train_step(self, state, action, reward, next_state):
        """单步训练"""
        self.update_q_value(state, action, reward, next_state)
        
        # 探索率衰减
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
    
    def autonomous_trading_loop(self, iterations=100):
        """自主交易循环"""
        print(f"🤖 启动AI自治代理交易系统")
        print(f"💰 初始资金: ${self.initial_capital}")
        print(f"⚡ 杠杆倍数: {self.leverage}x")
        print(f"📊 最大仓位: {self.max_position_pct*100}%")
        
        for i in range(iterations):
            # 风险检查
            risk_ok, reason = self.check_risk_limits()
            if not risk_ok:
                print(f"⚠️ 触发风险限制: {reason}")
                break
            
            # 扫描机会
            opportunities = self.high_frequency_scan()
            
            if opportunities:
                # 选择最佳机会
                best = max(opportunities, key=lambda x: x['spread'])
                
                # 获取状态并选择动作
                market_data = self.get_market_data(best['symbol'])
                if market_data:
                    state = self.get_state(market_data)
                    action = self.choose_action(state)
                    
                    if action != 'hold':
                        # 执行交易
                        quantity = self.calculate_position_size(market_data['price'])
                        result = self.execute_trade(best['symbol'], action, quantity, market_data['price'])
                        
                        if result:
                            # 计算奖励并学习
                            reward = self.calculate_reward(result, market_data)
                            self.train_step(state, action, reward, state)
                            
                            # 更新资金
                            if action == 'buy':
                                self.current_capital += reward
                            self.total_trades += 1
                            
                            print(f"🔄 交易 #{self.total_trades}: {action} {best['symbol']} @ ${market_data['price']:.2f} | 奖励: {reward:.4f}")
            
            # 间隔
            time.sleep(self.tick_interval)
            
            # 每10轮输出统计
            if (i + 1) % 10 == 0:
                win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
                print(f"📈 第{i+1}轮: 资金=${self.current_capital:.2f} | 交易数={self.total_trades} | 胜率={win_rate:.1f}%")
        
        # 最终报告
        self.print_final_report()
    
    def print_final_report(self):
        """输出最终报告"""
        print("\n" + "="*50)
        print("📊 AI自治代理交易报告")
        print("="*50)
        print(f"💰 最终资金: ${self.current_capital:.2f}")
        print(f"📈 总收益: ${self.current_capital - self.initial_capital:.2f}")
        print(f"📊 收益率: {((self.current_capital/self.initial_capital)-1)*100:.2f}%")
        print(f"🔢 总交易次数: {self.total_trades}")
        print(f"🎯 胜率: {(self.winning_trades/self.total_trades*100) if self.total_trades > 0 else 0:.1f}%")
        print(f"📚 Q表状态数: {len(self.q_table)}")
        print(f"🎲 最终探索率: {self.epsilon:.4f}")
        print("="*50)
        
        # 保存统计
        self.stats['final_capital'] = self.current_capital
        self.stats['total_return'] = self.current_capital - self.initial_capital
        self.stats['return_pct'] = ((self.current_capital/self.initial_capital)-1)*100
        
        with open('agent_trading_stats.json', 'w') as f:
            json.dump(self.stats, f, indent=2)


class ScalpingStrategy:
    """极速剥头皮策略 - 适用于小额高倍"""
    
    def __init__(self, min_spread=0.0005, profit_target=0.001):
        self.min_spread = min_spread  # 最小价差0.05%
        self.profit_target = profit_target  # 目标利润0.1%
        self.max_holding_time = 5  # 最大持仓5秒
    
    def find_opportunities(self, market_data_list):
        """寻找剥头皮机会"""
        opportunities = []
        
        for data in market_data_list:
            if data['spread'] >= self.min_spread:
                # 买入价差策略
                opportunities.append({
                    'strategy': 'scalp',
                    'symbol': data['symbol'],
                    'entry_spread': data['spread'],
                    'entry_price': data['ask'],
                    'target_price': data['bid'] * (1 + self.profit_target)
                })
        
        return opportunities


class MartingaleMultiplier:
    """马丁格尔仓位管理器 - 亏损后翻倍"""
    
    def __init__(self, base_quantity=1, max_multiplier=8):
        self.base_quantity = base_quantity
        self.max_multiplier = max_multiplier
        self.current_multiplier = 1
        self.loss_streak = 0
    
    def get_quantity(self):
        """获取当前仓位"""
        return self.base_quantity * self.current_multiplier
    
    def on_win(self):
        """盈利后重置"""
        self.current_multiplier = 1
        self.loss_streak = 0
    
    def on_loss(self):
        """亏损后翻倍"""
        if self.current_multiplier < self.max_multiplier:
            self.current_multiplier *= 2
            self.loss_streak += 1


# 主程序入口
if __name__ == "__main__":
    print("🦊 Web3Million AI自治代理系统 v1.0")
    print("="*50)
    
    # 创建AI代理交易系统
    agent = AIAgentTradingSystem(
        initial_capital=10,  # 小额启动$10
        leverage=10  # 10倍杠杆
    )
    
    # 运行高频交易
    agent.autonomous_trading_loop(iterations=50)
