"""
高级交易决策机制
深化优化交易策略，包含多维度分析和智能决策
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import asyncio
import ccxt.async_support as ccxt_async
from datetime import datetime, timedelta
import json
import math
from dataclasses import dataclass
from enum import Enum

class SignalStrength(Enum):
    """信号强度枚举"""
    WEAK = 1
    MODERATE = 2
    STRONG = 3
    VERY_STRONG = 4

class PositionSide(Enum):
    """持仓方向"""
    LONG = "long"
    SHORT = "short"
    NEUTRAL = "neutral"

@dataclass
class TradingSignal:
    """交易信号数据类"""
    symbol: str
    signal_type: str  # buy, sell, hold
    strength: SignalStrength
    entry_price: float
    target_price: float
    stop_loss: float
    confidence: float  # 0-1
    timestamp: datetime
    indicators: Dict

@dataclass
class Position:
    """持仓数据类"""
    symbol: str
    side: PositionSide
    size: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float
    leverage: float
    timestamp: datetime

class TechnicalAnalyzer:
    """技术分析器"""
    
    def __init__(self):
        self.lookback_period = 100  # 回看周期
    
    def calculate_sma(self, prices: List[float], period: int) -> float:
        """计算简单移动平均线"""
        if len(prices) < period:
            return prices[-1] if prices else 0
        return sum(prices[-period:]) / period
    
    def calculate_ema(self, prices: List[float], period: int) -> float:
        """计算指数移动平均线"""
        if len(prices) < period:
            return prices[-1] if prices else 0
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price - ema) * multiplier + ema
        
        return ema
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """计算相对强弱指数RSI"""
        if len(prices) < period + 1:
            return 50  # 中性值
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def calculate_macd(self, prices: List[float]) -> Tuple[float, float, float]:
        """计算MACD指标"""
        if len(prices) < 26:
            return 0, 0, 0
        
        ema12 = self.calculate_ema(prices[-26:], 12)
        ema26 = self.calculate_ema(prices[-26:], 26)
        
        macd_line = ema12 - ema26
        signal_line = self.calculate_ema([macd_line], 9)  # 简化计算
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    def calculate_bollinger_bands(self, prices: List[float], period: int = 20, std_dev: float = 2) -> Tuple[float, float, float]:
        """计算布林带"""
        if len(prices) < period:
            current_price = prices[-1] if prices else 0
            return current_price, current_price, current_price
        
        sma = self.calculate_sma(prices[-period:], period)
        variance = sum((price - sma) ** 2 for price in prices[-period:]) / period
        std = math.sqrt(variance)
        
        upper_band = sma + (std_dev * std)
        lower_band = sma - (std_dev * std)
        
        return upper_band, sma, lower_band

class MarketSentimentAnalyzer:
    """市场情绪分析器"""
    
    def analyze_price_action(self, prices: List[float], volumes: List[float]) -> Dict:
        """分析价格行为"""
        if len(prices) < 10:
            return {"sentiment": 0, "volatility": 0, "momentum": 0}
        
        # 计算波动率
        returns = [prices[i]/prices[i-1] - 1 for i in range(1, len(prices))]
        volatility = np.std(returns) * np.sqrt(252)  # 年化波动率
        
        # 计算动量
        momentum = prices[-1] / prices[0] - 1 if prices[0] != 0 else 0
        
        # 计算成交量加权情绪
        avg_volume = sum(volumes) / len(volumes) if volumes else 1
        volume_momentum = sum(v * (p - prices[0]) for v, p in zip(volumes, prices)) / (len(prices) * avg_volume) if avg_volume != 0 else 0
        
        sentiment_score = (momentum + volume_momentum) / 2
        
        return {
            "sentiment": sentiment_score,
            "volatility": volatility,
            "momentum": momentum,
            "volume_momentum": volume_momentum
        }
    
    def detect_patterns(self, prices: List[float]) -> List[str]:
        """检测技术形态"""
        patterns = []
        
        if len(prices) < 5:
            return patterns
        
        # 简单的双顶/双底检测
        recent_prices = prices[-5:]
        if len(set(recent_prices)) > 2:  # 至少3个不同价格
            max_idx = recent_prices.index(max(recent_prices))
            min_idx = recent_prices.index(min(recent_prices))
            
            if max_idx == 0 and max_idx == len(recent_prices) - 1:
                patterns.append("potential_double_top")
            elif min_idx == 0 and min_idx == len(recent_prices) - 1:
                patterns.append("potential_double_bottom")
        
        return patterns

class RiskManager:
    """风险管理器"""
    
    def __init__(self, initial_capital: float = 10000):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.max_position_size = 0.02  # 最大仓位2%
        self.max_daily_loss = 0.05    # 最大日亏损5%
        self.max_drawdown = 0.15      # 最大回撤15%
        self.daily_loss = 0
        self.total_loss = 0
        
    def calculate_position_size(self, entry_price: float, stop_loss: float, symbol: str = "BTC/USDT") -> float:
        """计算仓位大小"""
        # 基于风险的资金管理
        risk_per_trade = self.current_capital * 0.005  # 每笔交易风险0.5%
        price_risk = abs(entry_price - stop_loss)
        
        if price_risk == 0:
            return 0
        
        position_size = risk_per_trade / price_risk
        
        # 限制最大仓位
        max_size_by_capital = self.current_capital * self.max_position_size / entry_price
        position_size = min(position_size, max_size_by_capital)
        
        return position_size
    
    def should_trade(self, entry_price: float, stop_loss: float, side: PositionSide) -> bool:
        """判断是否应该交易"""
        # 检查当日亏损
        if self.daily_loss >= self.current_capital * self.max_daily_loss:
            return False
        
        # 检查最大回撤
        if self.total_loss >= self.initial_capital * self.max_drawdown:
            return False
        
        # 检查风险回报比
        risk = abs(entry_price - stop_loss)
        if risk == 0:
            return False
        
        # 确保风险可控
        return True
    
    def update_capital(self, pnl: float):
        """更新资金"""
        self.current_capital += pnl
        if pnl < 0:
            self.daily_loss -= pnl  # pnl为负时，减去负值等于加上正值
            self.total_loss -= pnl

class AdvancedTradingStrategy:
    """高级交易策略"""
    
    def __init__(self, initial_capital: float = 10000):
        self.technical_analyzer = TechnicalAnalyzer()
        self.sentiment_analyzer = MarketSentimentAnalyzer()
        self.risk_manager = RiskManager(initial_capital)
        self.positions = {}
        self.trades_history = []
        
    def generate_signals(self, symbol: str, historical_data: Dict) -> Optional[TradingSignal]:
        """生成交易信号"""
        prices = historical_data.get('prices', [])
        volumes = historical_data.get('volumes', [])
        
        if len(prices) < 20:
            return None
        
        current_price = prices[-1]
        
        # 技术指标计算
        sma_short = self.technical_analyzer.calculate_sma(prices, 10)
        sma_long = self.technical_analyzer.calculate_sma(prices, 20)
        rsi = self.technical_analyzer.calculate_rsi(prices)
        bb_upper, bb_middle, bb_lower = self.technical_analyzer.calculate_bollinger_bands(prices)
        
        # MACD
        macd_line, signal_line, histogram = self.technical_analyzer.calculate_macd(prices)
        
        # 市场情绪分析
        sentiment_data = self.sentiment_analyzer.analyze_price_action(prices, volumes)
        patterns = self.sentiment_analyzer.detect_patterns(prices)
        
        # 生成交易信号
        signal_type = "hold"
        strength = SignalStrength.WEAK
        confidence = 0.0
        
        # 多重指标确认策略
        bullish_signals = 0
        bearish_signals = 0
        
        # SMA金叉死叉
        if sma_short > sma_long and sma_short > sma_long:
            bullish_signals += 1
        elif sma_short < sma_long:
            bearish_signals += 1
        
        # RSI超买超卖
        if rsi < 30:  # 超卖
            bullish_signals += 1
        elif rsi > 70:  # 超买
            bearish_signals += 1
        
        # 布林带突破
        if current_price < bb_lower:  # 价格突破下轨
            bullish_signals += 1
        elif current_price > bb_upper:  # 价格突破上轨
            bearish_signals += 1
        
        # MACD信号
        if macd_line > signal_line:
            bullish_signals += 1
        else:
            bearish_signals += 1
        
        # 情绪分析
        if sentiment_data['sentiment'] > 0.1:
            bullish_signals += 1
        elif sentiment_data['sentiment'] < -0.1:
            bearish_signals += 1
        
        # 生成信号
        if bullish_signals >= 3:  # 至少3个指标确认
            signal_type = "buy"
            if bullish_signals >= 4:
                strength = SignalStrength.VERY_STRONG
            elif bullish_signals >= 3:
                strength = SignalStrength.STRONG
            else:
                strength = SignalStrength.MODERATE
            confidence = min(1.0, bullish_signals / 5.0)
        elif bearish_signals >= 3:  # 至少3个指标确认
            signal_type = "sell"
            if bearish_signals >= 4:
                strength = SignalStrength.VERY_STRONG
            elif bearish_signals >= 3:
                strength = SignalStrength.STRONG
            else:
                strength = SignalStrength.MODERATE
            confidence = min(1.0, bearish_signals / 5.0)
        
        if signal_type != "hold":
            # 计算入场价、目标价和止损价
            entry_price = current_price
            stop_loss = entry_price * 0.98 if signal_type == "buy" else entry_price * 1.02  # 2%止损
            target_price = entry_price * 1.04 if signal_type == "buy" else entry_price * 0.96  # 4%目标
            
            indicators = {
                'sma_short': sma_short,
                'sma_long': sma_long,
                'rsi': rsi,
                'bb_upper': bb_upper,
                'bb_middle': bb_middle,
                'bb_lower': bb_lower,
                'macd_line': macd_line,
                'signal_line': signal_line,
                'histogram': histogram,
                'sentiment': sentiment_data['sentiment'],
                'volatility': sentiment_data['volatility'],
                'momentum': sentiment_data['momentum'],
                'patterns': patterns
            }
            
            return TradingSignal(
                symbol=symbol,
                signal_type=signal_type,
                strength=strength,
                entry_price=entry_price,
                target_price=target_price,
                stop_loss=stop_loss,
                confidence=confidence,
                timestamp=datetime.now(),
                indicators=indications
            )
        
        return None
    
    def execute_trade(self, signal: TradingSignal) -> Optional[Position]:
        """执行交易"""
        if not self.risk_manager.should_trade(signal.entry_price, signal.stop_loss, 
                                            PositionSide.LONG if signal.signal_type == "buy" else PositionSide.SHORT):
            return None
        
        # 计算仓位大小
        position_size = self.risk_manager.calculate_position_size(
            signal.entry_price, signal.stop_loss, signal.symbol
        )
        
        if position_size <= 0:
            return None
        
        # 创建持仓
        side = PositionSide.LONG if signal.signal_type == "buy" else PositionSide.SHORT
        position = Position(
            symbol=signal.symbol,
            side=side,
            size=position_size,
            entry_price=signal.entry_price,
            current_price=signal.entry_price,
            unrealized_pnl=0,
            realized_pnl=0,
            leverage=1.0,
            timestamp=datetime.now()
        )
        
        self.positions[signal.symbol] = position
        self.trades_history.append({
            'symbol': signal.symbol,
            'side': signal.signal_type,
            'size': position_size,
            'price': signal.entry_price,
            'timestamp': signal.timestamp,
            'confidence': signal.confidence
        })
        
        return position
    
    def update_positions(self, current_prices: Dict[str, float]):
        """更新持仓"""
        for symbol, position in self.positions.items():
            if symbol in current_prices:
                current_price = current_prices[symbol]
                position.current_price = current_price
                
                # 计算未实现盈亏
                if position.side == PositionSide.LONG:
                    pnl = (current_price - position.entry_price) * position.size
                else:
                    pnl = (position.entry_price - current_price) * position.size
                
                position.unrealized_pnl = pnl
    
    def should_close_position(self, position: Position, current_price: float) -> bool:
        """判断是否应该平仓"""
        # 止损检查
        if position.side == PositionSide.LONG:
            if current_price <= position.stop_loss:
                return True
        else:
            if current_price >= position.stop_loss:
                return True
        
        # 止盈检查
        if position.side == PositionSide.LONG:
            if current_price >= position.target_price:
                return True
        else:
            if current_price <= position.target_price:
                return True
        
        return False

class PortfolioOptimizer:
    """投资组合优化器"""
    
    def __init__(self):
        self.correlation_threshold = 0.7  # 相关性阈值
        self.max_sector_allocation = 0.3   # 最大行业配置
    
    def optimize_allocation(self, signals: List[TradingSignal], available_capital: float) -> Dict[str, float]:
        """优化资金分配"""
        allocations = {}
        
        # 根据信号强度分配权重
        total_strength = sum(signal.strength.value * signal.confidence for signal in signals)
        if total_strength == 0:
            return allocations
        
        for signal in signals:
            weight = (signal.strength.value * signal.confidence) / total_strength
            allocations[signal.symbol] = available_capital * weight * 0.8  # 保留20%现金
        
        return allocations

def main():
    """主函数 - 演示高级交易策略"""
    print("🚀 启动高级交易决策机制")
    print("="*60)
    
    # 创建策略实例
    strategy = AdvancedTradingStrategy(initial_capital=10000)
    
    # 模拟历史数据
    print("📊 准备模拟市场数据...")
    mock_prices = [66000, 66200, 66100, 66500, 66800, 66700, 67000, 67200, 67100, 67300,
                   67500, 67400, 67600, 67800, 67700, 67900, 68000, 67950, 68100, 68200,
                   68150, 68300, 68400, 68350, 68500, 68600, 68550, 68700, 68800, 68750]
    mock_volumes = [1000, 1200, 900, 1100, 1300, 1000, 1400, 1200, 1100, 1300,
                    1500, 1200, 1400, 1600, 1300, 1500, 1700, 1400, 1600, 1800,
                    1500, 1700, 1900, 1600, 1800, 2000, 1700, 1900, 2100, 1800]
    
    historical_data = {
        'prices': mock_prices,
        'volumes': mock_volumes
    }
    
    print(f"📈 模拟数据: {len(mock_prices)} 个价格点")
    print(f"💰 初始资金: ${strategy.risk_manager.initial_capital:,.2f}")
    
    # 生成交易信号
    print("\n🔍 生成交易信号...")
    signal = strategy.generate_signals("BTC/USDT", historical_data)
    
    if signal:
        print(f"🎯 生成交易信号: {signal.signal_type.upper()} {signal.symbol}")
        print(f"📊 信号强度: {signal.strength.name}")
        print(f"📈 入场价: ${signal.entry_price:,.2f}")
        print(f"🎯 目标价: ${signal.target_price:,.2f}")
        print(f"🛑 止损价: ${signal.stop_loss:,.2f}")
        print(f"💯 置信度: {signal.confidence:.2f}")
        
        # 执行交易
        print("\n💼 执行交易...")
        position = strategy.execute_trade(signal)
        if position:
            print(f"✅ 交易执行成功: {position.size:.6f} {position.symbol}")
            print(f"💰 仓位价值: ${position.size * position.entry_price:,.2f}")
        else:
            print("❌ 交易未执行（风险控制）")
    else:
        print("❌ 未生成有效交易信号")
    
    # 展示技术指标
    print("\n📊 技术指标分析:")
    analyzer = TechnicalAnalyzer()
    
    sma_short = analyzer.calculate_sma(mock_prices, 10)
    sma_long = analyzer.calculate_sma(mock_prices, 20)
    rsi = analyzer.calculate_rsi(mock_prices)
    bb_upper, bb_middle, bb_lower = analyzer.calculate_bollinger_bands(mock_prices)
    
    print(f"   SMA(10): ${sma_short:,.2f}")
    print(f"   SMA(20): ${sma_long:,.2f}")
    print(f"   RSI(14): {rsi:.2f}")
    print(f"   BB Upper: ${bb_upper:,.2f}")
    print(f"   BB Middle: ${bb_middle:,.2f}")
    print(f"   BB Lower: ${bb_lower:,.2f}")
    
    print("\n🎯 高级交易决策机制已优化完成!")
    print("💡 系统现在具备多维度分析和智能决策能力")
    
    return strategy

if __name__ == "__main__":
    strategy_instance = main()