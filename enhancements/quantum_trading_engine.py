"""
量子交易引擎增强模块
集成最新的量化交易机制和自我进化AI agent功能
"""

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.distributions import Normal
import random
from typing import Dict, List, Tuple, Any
import asyncio
import ccxt.async_support as ccxt_async
from datetime import datetime, timedelta
import json
import os


class ActorNetwork(nn.Module):
    """演员网络 - 用于选择动作"""
    def __init__(self, input_dim: int, output_dim: int, hidden_dim: int = 256):
        super(ActorNetwork, self).__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc_mean = nn.Linear(hidden_dim, output_dim)
        self.fc_std = nn.Linear(hidden_dim, output_dim)
        self.tanh = nn.Tanh()
        
    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        mean = self.tanh(self.fc_mean(x))  # 输出范围[-1, 1]
        std = torch.sigmoid(self.fc_std(x)) + 1e-5  # 确保std为正值
        return mean, std


class CriticNetwork(nn.Module):
    """评论家网络 - 用于评估状态价值"""
    def __init__(self, input_dim: int, hidden_dim: int = 256):
        super(CriticNetwork, self).__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, 1)
        
    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        value = self.fc3(x)
        return value


class DeepReinforcementTrader:
    """深度强化学习交易者"""
    
    def __init__(self, input_dim: int, action_dim: int, lr_actor: float = 3e-4, lr_critic: float = 1e-3):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        self.actor = ActorNetwork(input_dim, action_dim).to(self.device)
        self.critic = CriticNetwork(input_dim).to(self.device)
        
        self.optimizer_actor = optim.Adam(self.actor.parameters(), lr=lr_actor)
        self.optimizer_critic = optim.Adam(self.critic.parameters(), lr=lr_critic)
        
        self.gamma = 0.99  # 折扣因子
        self.eps_clip = 0.2  # PPO裁剪参数
        self.entropy_coeff = 0.01  # 熵系数
        
    def select_action(self, state: np.ndarray) -> Tuple[np.ndarray, float]:
        """选择动作"""
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            mean, std = self.actor(state_tensor)
            dist = Normal(mean, std)
            action = dist.sample()
            log_prob = dist.log_prob(action).sum(dim=-1)
        
        return action.cpu().numpy()[0], log_prob.item()
    
    def update(self, states: List[np.ndarray], actions: List[np.ndarray], 
               rewards: List[float], next_states: List[np.ndarray], dones: List[bool]):
        """更新网络参数"""
        states = torch.FloatTensor(states).to(self.device)
        actions = torch.FloatTensor(actions).to(self.device)
        rewards = torch.FloatTensor(rewards).to(self.device)
        next_states = torch.FloatTensor(next_states).to(self.device)
        dones = torch.BoolTensor(dones).to(self.device)
        
        # 计算目标价值
        with torch.no_grad():
            next_values = self.critic(next_states).squeeze(-1)
            target_values = rewards + self.gamma * next_values * (~dones)
        
        # 更新评论家
        current_values = self.critic(states).squeeze(-1)
        critic_loss = nn.MSELoss()(current_values, target_values)
        
        self.optimizer_critic.zero_grad()
        critic_loss.backward()
        self.optimizer_critic.step()
        
        # 更新演员
        mean, std = self.actor(states)
        dist = Normal(mean, std)
        log_probs = dist.log_prob(actions).sum(dim=-1)
        
        advantages = target_values - current_values.detach()
        actor_loss = -(log_probs * advantages.detach()).mean()
        
        # 添加熵正则化
        entropy = dist.entropy().sum(dim=-1).mean()
        actor_loss -= self.entropy_coeff * entropy
        
        self.optimizer_actor.zero_grad()
        actor_loss.backward()
        self.optimizer_actor.step()


class TimeSeriesPredictor:
    """时间序列预测器"""
    
    def __init__(self, sequence_length: int = 50, prediction_horizon: int = 10):
        self.sequence_length = sequence_length
        self.prediction_horizon = prediction_horizon
        self.model = self._build_model()
        
    def _build_model(self):
        """构建预测模型（这里简化为线性回归，实际可使用LSTM/Transformer）"""
        # 在实际实现中，这里应该是更复杂的神经网络
        return LinearRegressionModel(self.sequence_length)
    
    def preprocess_data(self, prices: List[float]) -> np.ndarray:
        """预处理价格数据"""
        if len(prices) < self.sequence_length:
            raise ValueError(f"数据长度不足，需要至少{self.sequence_length}个点")
        
        # 创建滑动窗口
        sequences = []
        for i in range(len(prices) - self.sequence_length + 1):
            seq = prices[i:i + self.sequence_length]
            # 归一化
            normalized_seq = (np.array(seq) - np.mean(seq)) / (np.std(seq) + 1e-8)
            sequences.append(normalized_seq)
        
        return np.array(sequences)
    
    def predict(self, historical_prices: List[float]) -> Dict[str, float]:
        """预测未来价格方向"""
        try:
            sequences = self.preprocess_data(historical_prices)
            latest_sequence = sequences[-1:]  # 使用最新序列
            
            # 简化预测逻辑（实际应使用训练好的模型）
            # 这里使用移动平均作为示例
            ma_short = np.mean(historical_prices[-5:])
            ma_long = np.mean(historical_prices[-20:])
            
            signal_strength = (ma_short - ma_long) / ma_long
            confidence = min(abs(signal_strength) * 10, 1.0)  # 限制置信度在0-1之间
            
            return {
                'direction': 1.0 if signal_strength > 0 else -1.0,  # 1为上涨，-1为下跌
                'confidence': confidence,
                'expected_return': signal_strength * 0.02  # 假设2%的基础预期
            }
        except Exception as e:
            print(f"预测时出错: {e}")
            return {
                'direction': 0.0,
                'confidence': 0.0,
                'expected_return': 0.0
            }


class LinearRegressionModel:
    """线性回归模型（简化版）"""
    def __init__(self, input_dim: int):
        self.weights = np.random.randn(input_dim) * 0.01
        self.bias = 0.0
        
    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测"""
        return np.dot(X, self.weights) + self.bias


class GeneticOptimizer:
    """遗传算法优化器"""
    
    def __init__(self, population_size: int = 50, mutation_rate: float = 0.1, crossover_rate: float = 0.8):
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.population = []
        
    def initialize_population(self, param_ranges: Dict[str, Tuple[float, float]]) -> List[Dict[str, float]]:
        """初始化种群"""
        population = []
        for _ in range(self.population_size):
            individual = {}
            for param, (min_val, max_val) in param_ranges.items():
                individual[param] = random.uniform(min_val, max_val)
            population.append(individual)
        self.population = population
        return population
    
    def evaluate_fitness(self, individual: Dict[str, float], market_data: Any) -> float:
        """评估个体适应度（简化版）"""
        # 在实际实现中，这里应该运行回测来评估策略表现
        # 这里使用简化的适应度函数
        score = 0.0
        
        # 基于参数的简单评分
        if 'risk_factor' in individual:
            risk_factor = individual['risk_factor']
            score -= abs(risk_factor - 0.05) * 10  # 偏好风险因子接近0.05
        
        if 'position_size' in individual:
            position_size = individual['position_size']
            score += min(position_size * 100, 10)  # 偏好适度的仓位大小
        
        return score
    
    def selection(self, fitness_scores: List[float]) -> List[int]:
        """选择操作（锦标赛选择）"""
        selected_indices = []
        tournament_size = 3
        
        for _ in range(self.population_size):
            tournament_indices = random.choices(range(len(fitness_scores)), k=tournament_size)
            winner_idx = max(tournament_indices, key=lambda idx: fitness_scores[idx])
            selected_indices.append(winner_idx)
        
        return selected_indices
    
    def crossover(self, parent1: Dict[str, float], parent2: Dict[str, float]) -> Tuple[Dict[str, float], Dict[str, float]]:
        """交叉操作"""
        if random.random() > self.crossover_rate:
            return parent1.copy(), parent2.copy()
        
        child1, child2 = {}, {}
        for param in parent1.keys():
            if random.random() < 0.5:
                child1[param] = parent1[param]
                child2[param] = parent2[param]
            else:
                child1[param] = parent2[param]
                child2[param] = parent1[param]
        
        return child1, child2
    
    def mutate(self, individual: Dict[str, float], param_ranges: Dict[str, Tuple[float, float]]) -> Dict[str, float]:
        """变异操作"""
        mutated = individual.copy()
        for param, (min_val, max_val) in param_ranges.items():
            if random.random() < self.mutation_rate:
                # 小幅度随机扰动
                current_val = mutated[param]
                perturbation = random.gauss(0, (max_val - min_val) * 0.1)
                mutated[param] = max(min_val, min(max_val, current_val + perturbation))
        
        return mutated
    
    def evolve_generation(self, market_data: Any, param_ranges: Dict[str, Tuple[float, float]]) -> Dict[str, float]:
        """进化一代"""
        if not self.population:
            self.initialize_population(param_ranges)
        
        # 评估适应度
        fitness_scores = []
        for individual in self.population:
            fitness = self.evaluate_fitness(individual, market_data)
            fitness_scores.append(fitness)
        
        # 选择
        selected_indices = self.selection(fitness_scores)
        new_population = []
        
        # 交叉和变异
        for i in range(0, len(selected_indices), 2):
            parent1_idx = selected_indices[i]
            parent2_idx = selected_indices[i + 1] if i + 1 < len(selected_indices) else selected_indices[0]
            
            parent1 = self.population[parent1_idx]
            parent2 = self.population[parent2_idx]
            
            child1, child2 = self.crossover(parent1, parent2)
            child1 = self.mutate(child1, param_ranges)
            child2 = self.mutate(child2, param_ranges)
            
            new_population.extend([child1, child2])
        
        # 确保种群大小一致
        self.population = new_population[:self.population_size]
        
        # 返回最佳个体
        best_idx = max(range(len(fitness_scores)), key=lambda i: fitness_scores[i])
        return self.population[best_idx].copy()


class QuantumTradingEngine:
    """量子交易引擎 - 集成所有先进机制"""
    
    def __init__(self, initial_capital: float = 10000.0):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.position_size = 0.0
        self.max_position_size = 0.1  # 最大仓位10%
        
        # 初始化各组件
        self.rl_trader = DeepReinforcementTrader(input_dim=10, action_dim=3)  # 3个动作：买入、卖出、持有
        self.time_series_predictor = TimeSeriesPredictor()
        self.genetic_optimizer = GeneticOptimizer()
        
        # 市场数据缓存
        self.price_history = []
        self.volume_history = []
        self.indicators = {}
        
        # 风险管理
        self.max_drawdown = 0.15  # 最大回撤15%
        self.current_drawdown = 0.0
        self.best_equity = initial_capital
        
        # 交易统计
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.profit_factor = 0.0
        
    def update_market_data(self, price: float, volume: float = None):
        """更新市场数据"""
        self.price_history.append(price)
        if volume:
            self.volume_history.append(volume)
        
        # 保持历史数据在合理范围内
        max_history = 1000
        if len(self.price_history) > max_history:
            self.price_history = self.price_history[-max_history:]
            if self.volume_history:
                self.volume_history = self.volume_history[-max_history:]
    
    def calculate_technical_indicators(self) -> Dict[str, float]:
        """计算技术指标"""
        if len(self.price_history) < 20:
            return {}
        
        prices = np.array(self.price_history)
        
        # 简单移动平均
        sma_short = np.mean(prices[-5:])
        sma_long = np.mean(prices[-20:])
        
        # RSI
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-14:]) if len(gains) >= 14 else 0.5
        avg_loss = np.mean(losses[-14:]) if len(losses) >= 14 else 0.5
        
        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        # 波动率
        volatility = np.std(np.diff(prices)) if len(prices) > 1 else 0
        
        return {
            'sma_short': sma_short,
            'sma_long': sma_long,
            'rsi': rsi,
            'volatility': volatility,
            'price': prices[-1]
        }
    
    def get_state_vector(self) -> np.ndarray:
        """获取状态向量供RL模型使用"""
        indicators = self.calculate_technical_indicators()
        
        if not indicators:
            # 返回默认状态
            return np.zeros(10)
        
        # 构建状态向量
        state = np.array([
            indicators.get('sma_short', 0),
            indicators.get('sma_long', 0),
            indicators.get('rsi', 50) / 100,  # 归一化到[0,1]
            indicators.get('volatility', 0),
            indicators.get('price', 0),
            self.position_size / self.max_position_size if self.max_position_size > 0 else 0,  # 当前仓位比例
            self.current_drawdown,
            self.total_trades / 1000,  # 归一化交易次数
            self.winning_trades / max(self.total_trades, 1),  # 胜率
            self.profit_factor / 10  # 归一化利润因子
        ])
        
        return np.clip(state, -1, 1)  # 限制在[-1, 1]范围内
    
    def execute_trade(self, action: int, predicted_direction: float = 0):
        """执行交易"""
        if len(self.price_history) == 0:
            return
        
        current_price = self.price_history[-1]
        
        # 动作: 0=卖出, 1=持有, 2=买入
        if action == 0:  # 卖出
            if self.position_size > 0:
                # 平仓
                pnl = self.position_size * (current_price - self.entry_price)
                self.current_capital += pnl
                self.position_size = 0
                
                if pnl > 0:
                    self.winning_trades += 1
                else:
                    self.losing_trades += 1
                self.total_trades += 1
                
                # 更新权益峰值和回撤
                if self.current_capital > self.best_equity:
                    self.best_equity = self.current_capital
                else:
                    self.current_drawdown = (self.best_equity - self.current_capital) / self.best_equity
        
        elif action == 2:  # 买入
            if self.position_size == 0:  # 只有在空仓时才开仓
                # 计算仓位大小（基于预测置信度和风险管理）
                confidence = abs(predicted_direction)
                risk_amount = self.current_capital * self.max_position_size * min(confidence, 1.0)
                self.position_size = risk_amount / current_price
                self.entry_price = current_price
                
                self.total_trades += 1
    
    def optimize_parameters(self):
        """使用遗传算法优化参数"""
        # 定义要优化的参数范围
        param_ranges = {
            'risk_factor': (0.01, 0.1),
            'position_size': (0.01, 0.2),
            'lookback_period': (10, 100),
            'prediction_confidence_threshold': (0.3, 0.8)
        }
        
        # 进化一代
        best_params = self.genetic_optimizer.evolve_generation(
            market_data={'prices': self.price_history},
            param_ranges=param_ranges
        )
        
        # 应用最佳参数
        self.max_position_size = best_params.get('position_size', self.max_position_size)
        
        return best_params
    
    async def run_cycle(self, current_price: float):
        """运行一个交易周期"""
        # 更新市场数据
        self.update_market_data(current_price)
        
        # 获取状态向量
        state = self.get_state_vector()
        
        # 使用时间序列预测器预测方向
        prediction = self.time_series_predictor.predict(self.price_history) if len(self.price_history) >= 50 else {
            'direction': 0.0,
            'confidence': 0.0,
            'expected_return': 0.0
        }
        
        # RL模型选择动作
        action, log_prob = self.rl_trader.select_action(state)
        action_idx = int(np.argmax(action))  # 转换为离散动作
        
        # 执行交易
        self.execute_trade(action_idx, prediction['direction'])
        
        # 定期优化参数
        if self.total_trades > 0 and self.total_trades % 50 == 0:
            optimized_params = self.optimize_parameters()
            print(f"🔄 参数优化完成: {optimized_params}")
        
        # 更新统计数据
        if self.current_capital > self.best_equity:
            self.best_equity = self.current_capital
        else:
            self.current_drawdown = (self.best_equity - self.current_capital) / self.best_equity
        
        if self.total_trades > 0:
            self.profit_factor = (self.winning_trades * 1.0) / max(self.losing_trades, 1)
        
        return {
            'capital': self.current_capital,
            'position_size': self.position_size,
            'action': action_idx,
            'prediction': prediction,
            'drawdown': self.current_drawdown,
            'win_rate': self.winning_trades / max(self.total_trades, 1)
        }


async def main():
    """主函数 - 演示量子交易引擎"""
    print("🔬 Web3Million 量子交易引擎增强版")
    print("="*50)
    
    # 创建引擎实例
    engine = QuantumTradingEngine(initial_capital=10000.0)
    
    # 模拟市场价格数据
    current_price = 100.0
    print(f"💰 初始资本: ${engine.initial_capital}")
    print(f"📊 初始价格: ${current_price}")
    
    # 运行多个交易周期
    for cycle in range(100):
        # 模拟价格变动（随机游走 + 趋势成分）
        trend = 0.001 if cycle % 20 < 10 else -0.0005  # 模拟短期趋势
        noise = np.random.normal(0, 0.02)  # 2%的标准差噪声
        price_change = trend + noise
        current_price *= (1 + price_change)
        
        # 运行交易周期
        result = await engine.run_cycle(current_price)
        
        if cycle % 10 == 0:
            print(f"\n📈 周期 {cycle}:")
            print(f"   价格: ${current_price:.2f}")
            print(f"   资本: ${result['capital']:.2f}")
            print(f"   仓位: {result['position_size']:.4f}")
            print(f"   预测: 方向={result['prediction']['direction']:.2f}, "
                  f"置信度={result['prediction']['confidence']:.2f}")
            print(f"   回撤: {result['drawdown']:.2%}")
            print(f"   胜率: {result['win_rate']:.2%}")
    
    print(f"\n🎯 最终结果:")
    print(f"   初始资本: ${engine.initial_capital:.2f}")
    print(f"   最终资本: ${result['capital']:.2f}")
    print(f"   总收益率: {(result['capital']/engine.initial_capital - 1)*100:.2f}%")
    print(f"   总交易数: {engine.total_trades}")
    print(f"   最大回撤: {engine.current_drawdown:.2%}")
    
    print(f"\n✅ 量子交易引擎演示完成!")


if __name__ == "__main__":
    asyncio.run(main())