"""
先进AI交易决策系统
深度优化的多维度智能交易策略
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
import asyncio
import ccxt.async_support as ccxt_async
from datetime import datetime, timedelta
import json
import math
import talib
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib
import pickle

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

class TradeType(Enum):
    """交易类型"""
    SWING = "swing"
    DAY = "day"
    SCALP = "scalp"
    POSITION = "position"

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
    trade_type: TradeType
    risk_reward_ratio: float
    expected_return: float

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
    stop_loss: float
    take_profit: float

class AdvancedTechnicalAnalyzer:
    """高级技术分析器"""
    
    def __init__(self):
        self.lookback_period = 200  # 更长的回看周期
    
    def calculate_indicators(self, df: pd.DataFrame) -> Dict:
        """计算所有技术指标"""
        if len(df) < 50:
            return {}
        
        high = df['high'].values.astype(float)
        low = df['low'].values.astype(float)
        close = df['close'].values.astype(float)
        volume = df['volume'].values.astype(float)
        
        indicators = {}
        
        # 移动平均线
        try:
            indicators['sma_10'] = talib.SMA(close, timeperiod=10)[-1]
            indicators['sma_20'] = talib.SMA(close, timeperiod=20)[-1]
            indicators['sma_50'] = talib.SMA(close, timeperiod=50)[-1]
            indicators['sma_200'] = talib.SMA(close, timeperiod=200)[-1]
        except:
            indicators['sma_10'] = close[-1]
            indicators['sma_20'] = close[-1]
            indicators['sma_50'] = close[-1]
            indicators['sma_200'] = close[-1]
        
        # 指数移动平均线
        try:
            indicators['ema_12'] = talib.EMA(close, timeperiod=12)[-1]
            indicators['ema_26'] = talib.EMA(close, timeperiod=26)[-1]
        except:
            indicators['ema_12'] = close[-1]
            indicators['ema_26'] = close[-1]
        
        # MACD
        try:
            macd, macd_signal, macd_hist = talib.MACD(close)
            indicators['macd'] = macd[-1]
            indicators['macd_signal'] = macd_signal[-1]
            indicators['macd_hist'] = macd_hist[-1]
        except:
            indicators['macd'] = 0
            indicators['macd_signal'] = 0
            indicators['macd_hist'] = 0
        
        # RSI
        try:
            indicators['rsi'] = talib.RSI(close, timeperiod=14)[-1]
        except:
            indicators['rsi'] = 50
        
        # 布林带
        try:
            bb_upper, bb_middle, bb_lower = talib.BBANDS(close)
            indicators['bb_upper'] = bb_upper[-1]
            indicators['bb_middle'] = bb_middle[-1]
            indicators['bb_lower'] = bb_lower[-1]
        except:
            indicators['bb_upper'] = close[-1] * 1.05
            indicators['bb_middle'] = close[-1]
            indicators['bb_lower'] = close[-1] * 0.95
        
        # KDJ指标
        try:
            k, d, j = talib.STOCH(high, low, close)
            indicators['stoch_k'] = k[-1]
            indicators['stoch_d'] = d[-1]
            indicators['stoch_j'] = j[-1]
        except:
            # 如果STOCH返回值不足，使用默认值
            indicators['stoch_k'] = 50
            indicators['stoch_d'] = 50
            indicators['stoch_j'] = 50
        
        # ADX (趋势强度)
        try:
            indicators['adx'] = talib.ADX(high, low, close, timeperiod=14)[-1]
        except:
            indicators['adx'] = 25
        
        # 威廉指标 (%R)
        try:
            indicators['willr'] = talib.WILLR(high, low, close, timeperiod=14)[-1]
        except:
            indicators['willr'] = -50
        
        # CCI (商品通道指数)
        try:
            indicators['cci'] = talib.CCI(high, low, close, timeperiod=14)[-1]
        except:
            indicators['cci'] = 0
        
        # ROC (价格变化率)
        try:
            indicators['roc'] = talib.ROC(close, timeperiod=10)[-1]
        except:
            indicators['roc'] = 0
        
        # OBV (能量潮)
        try:
            indicators['obv'] = talib.OBV(close, volume)[-1]
        except:
            indicators['obv'] = 0
        
        # 波动率
        try:
            indicators['atr'] = talib.ATR(high, low, close, timeperiod=14)[-1]
            indicators['stddev'] = talib.STDDEV(close, timeperiod=20)[-1]
        except:
            indicators['atr'] = close[-1] * 0.02
            indicators['stddev'] = 0.02
        
        # 价格位置
        try:
            current_price = close[-1]
            indicators['price_position_bb'] = (current_price - bb_lower[-1]) / (bb_upper[-1] - bb_lower[-1]) if bb_upper[-1] != bb_lower[-1] else 0.5
            indicators['price_position_high_low'] = (current_price - low[-14:].min()) / (high[-14:].max() - low[-14:].min()) if high[-14:].max() != low[-14:].min() else 0.5
        except:
            indicators['price_position_bb'] = 0.5
            indicators['price_position_high_low'] = 0.5
        
        return indicators
    
    def detect_patterns(self, df: pd.DataFrame) -> List[str]:
        """检测技术形态"""
        patterns = []
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        
        if len(close) < 5:
            return patterns
        
        # 检测顶部反转形态
        if self._detect_head_and_shoulders(df):
            patterns.append("head_and_shoulders")
        
        # 检测底部反转形态
        if self._detect_double_bottom(df):
            patterns.append("double_bottom")
        
        # 检测突破形态
        if self._detect_breakout(df):
            patterns.append("breakout")
        
        # 检测回调形态
        if self._detect_pullback(df):
            patterns.append("pullback")
        
        return patterns
    
    def _detect_head_and_shoulders(self, df: pd.DataFrame) -> bool:
        """检测头肩顶形态"""
        # 简化检测逻辑
        close = df['close'].values[-20:]  # 最近20个点
        if len(close) < 10:
            return False
        
        # 寻找峰值
        peaks = []
        for i in range(1, len(close)-1):
            if close[i-1] < close[i] > close[i+1]:
                peaks.append((i, close[i]))
        
        # 检查是否形成头肩顶结构
        if len(peaks) >= 3:
            # 简单检查中间峰最高，两边峰较低
            peak_values = [p[1] for p in peaks]
            if len(peak_values) >= 3:
                middle_peak = peak_values[1]
                left_peak = peak_values[0]
                right_peak = peak_values[2]
                if middle_peak > left_peak and middle_peak > right_peak:
                    return True
        
        return False
    
    def _detect_double_bottom(self, df: pd.DataFrame) -> bool:
        """检测双底形态"""
        close = df['close'].values[-20:]
        if len(close) < 10:
            return False
        
        # 寻找谷值
        troughs = []
        for i in range(1, len(close)-1):
            if close[i-1] > close[i] < close[i+1]:
                troughs.append((i, close[i]))
        
        # 检查是否形成双底结构
        if len(troughs) >= 2:
            trough_values = [t[1] for t in troughs]
            if len(trough_values) >= 2:
                # 检查两个谷值相近
                if abs(trough_values[0] - trough_values[1]) / min(trough_values[0], trough_values[1]) < 0.02:  # 2%以内
                    return True
        
        return False
    
    def _detect_breakout(self, df: pd.DataFrame) -> bool:
        """检测突破形态"""
        close = df['close'].values
        if len(close) < 20:
            return False
        
        # 计算20日高点
        recent_high = max(close[-20:-2])  # 前20日最高点（排除最近2日）
        current_price = close[-1]
        
        # 检查是否突破
        if current_price > recent_high * 1.01:  # 超过1%
            return True
        
        return False
    
    def _detect_pullback(self, df: pd.DataFrame) -> bool:
        """检测回调形态"""
        close = df['close'].values
        if len(close) < 20:
            return False
        
        # 计算趋势
        recent_high = max(close[-10:])
        recent_low = min(close[-10:])
        if len(close) > 20:
            prev_high = max(close[-20:-10])  # 前10天的高点
            trend_direction = recent_high > prev_high
        else:
            trend_direction = True
        
        # 检查回调
        current_price = close[-1]
        if trend_direction and current_price < recent_high * 0.95:  # 回调5%
            return True
        
        return False

class MachineLearningAnalyzer:
    """机器学习分析器"""
    
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
    
    def prepare_features(self, indicators: Dict) -> np.array:
        """准备特征数据"""
        feature_names = [
            'rsi', 'macd', 'macd_signal', 'macd_hist',
            'bb_upper', 'bb_middle', 'bb_lower', 'price_position_bb',
            'stoch_k', 'stoch_d', 'stoch_j',
            'adx', 'willr', 'cci', 'roc',
            'atr', 'stddev', 'obv'
        ]
        
        features = []
        for name in feature_names:
            if name in indicators:
                features.append(indicators[name])
            else:
                features.append(0)  # 缺省值
        
        return np.array(features).reshape(1, -1)
    
    def train_model(self, historical_data: List[Dict]) -> bool:
        """训练模型"""
        if len(historical_data) < 100:
            return False
        
        X = []
        y = []
        
        for data_point in historical_data:
            if 'future_return' in data_point and 'indicators' in data_point:
                features = self.prepare_features(data_point['indicators']).flatten()
                # 根据未来收益确定标签
                future_return = data_point['future_return']
                if future_return > 0.02:  # 2%以上收益
                    label = 1  # 买入
                elif future_return < -0.02:  # -2%以下收益
                    label = -1  # 卖出
                else:
                    label = 0  # 持有
                X.append(features)
                y.append(label)
        
        if len(X) < 50:
            return False
        
        X = np.array(X)
        y = np.array(y)
        
        # 标准化特征
        X_scaled = self.scaler.fit_transform(X)
        
        # 训练模型
        self.model.fit(X_scaled, y)
        self.is_trained = True
        
        return True
    
    def predict_signal(self, indicators: Dict) -> Tuple[int, float]:
        """预测信号"""
        if not self.is_trained:
            return 0, 0.5  # 默认持有，50%置信度
        
        features = self.prepare_features(indicators)
        features_scaled = self.scaler.transform(features)
        
        prediction = self.model.predict(features_scaled)[0]
        probability = self.model.predict_proba(features_scaled)[0].max()
        
        return prediction, probability

class AdvancedRiskManager:
    """高级风险管理器"""
    
    def __init__(self, initial_capital: float = 10000):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.max_position_size = 0.02  # 最大仓位2%
        self.max_daily_loss = 0.03    # 最大日亏损3%
        self.max_drawdown = 0.15      # 最大回撤15%
        self.daily_loss = 0
        self.total_loss = 0
        self.max_correlation = 0.7    # 最大相关性
        self.max_leverage = 1.0       # 最大杠杆
        
        # 动态风险调整
        self.volatility_multiplier = 1.0
        self.correlation_penalty = 0.0
    
    def calculate_position_size(self, entry_price: float, stop_loss: float, 
                              signal_confidence: float = 0.5, volatility: float = 0.02) -> float:
        """计算仓位大小（基于多种因素）"""
        # 基于风险的资金管理
        risk_per_trade = self.current_capital * 0.005  # 每笔交易风险0.5%
        price_risk = abs(entry_price - stop_loss)
        
        if price_risk == 0:
            return 0
        
        # 基础仓位计算
        base_position = risk_per_trade / price_risk
        
        # 信号置信度调整
        confidence_adjustment = signal_confidence
        
        # 波动率调整
        volatility_adjustment = max(0.5, min(1.5, 1.0 / (volatility * 50)))  # 波动率越高，仓位越小
        
        # 综合调整
        adjusted_position = base_position * confidence_adjustment * volatility_adjustment
        
        # 限制最大仓位
        max_size_by_capital = self.current_capital * self.max_position_size / entry_price
        final_position = min(adjusted_position, max_size_by_capital)
        
        return final_position
    
    def should_trade(self, entry_price: float, stop_loss: float, side: PositionSide,
                    correlation_risk: float = 0.0) -> bool:
        """判断是否应该交易（多维度风险评估）"""
        # 检查当日亏损
        if self.daily_loss >= self.current_capital * self.max_daily_loss:
            return False
        
        # 检查最大回撤
        if self.total_loss >= self.initial_capital * self.max_drawdown:
            return False
        
        # 检查相关性风险
        if correlation_risk > self.max_correlation:
            return False
        
        # 检查价格风险
        risk = abs(entry_price - stop_loss) / entry_price
        if risk > 0.10:  # 止损距离超过10%
            return False
        
        return True
    
    def calculate_stop_loss(self, entry_price: float, side: PositionSide, 
                          volatility: float, atr: float) -> float:
        """计算动态止损"""
        if side == PositionSide.LONG:
            # 多头止损：ATR倍数或固定百分比，取较大值
            atr_stop = entry_price - (atr * 2.0)  # 2倍ATR
            percent_stop = entry_price * 0.97  # 3%止损
            return max(atr_stop, percent_stop)
        else:
            # 空头止损
            atr_stop = entry_price + (atr * 2.0)
            percent_stop = entry_price * 1.03  # 3%止损
            return min(atr_stop, percent_stop)
    
    def calculate_take_profit(self, entry_price: float, side: PositionSide, 
                           risk_reward_ratio: float, stop_loss: float) -> float:
        """计算止盈"""
        risk = abs(entry_price - stop_loss)
        reward = risk * risk_reward_ratio
        
        if side == PositionSide.LONG:
            return entry_price + reward
        else:
            return entry_price - reward
    
    def update_capital(self, pnl: float):
        """更新资金"""
        self.current_capital += pnl
        if pnl < 0:
            self.daily_loss -= pnl  # pnl为负时，减去负值等于加上正值
            self.total_loss -= pnl

class AdaptivePortfolioManager:
    """自适应投资组合管理器"""
    
    def __init__(self):
        self.correlation_matrix = {}
        self.position_limits = {}
        self.rebalancing_threshold = 0.05  # 5%再平衡阈值
    
    def optimize_allocation(self, signals: List[TradingSignal], 
                          available_capital: float, correlations: Dict = None) -> Dict[str, float]:
        """优化资金分配（考虑相关性）"""
        if not signals:
            return {}
        
        # 根据信号强度和置信度分配权重
        total_score = 0
        signal_scores = []
        
        for signal in signals:
            score = signal.strength.value * signal.confidence * signal.expected_return
            signal_scores.append((signal, score))
            total_score += score
        
        if total_score == 0:
            return {}
        
        allocations = {}
        for signal, score in signal_scores:
            weight = score / total_score
            # 应用相关性调整
            if correlations and signal.symbol in correlations:
                correlation_factor = 1 - min(0.5, correlations[signal.symbol] / 2)  # 相关性越高，分配越少
                weight *= correlation_factor
            
            allocations[signal.symbol] = available_capital * weight * 0.9  # 保留10%现金
        
        return allocations
    
    def calculate_correlations(self, price_data: Dict[str, List[float]]) -> Dict[str, float]:
        """计算相关性矩阵"""
        correlations = {}
        
        if len(price_data) < 2:
            return correlations
        
        symbols = list(price_data.keys())
        
        for symbol in symbols:
            if len(price_data[symbol]) < 10:
                continue
            
            # 计算该符号与其他符号的相关性
            symbol_returns = np.diff(price_data[symbol]) / price_data[symbol][:-1]
            max_corr = 0
            
            for other_symbol in symbols:
                if symbol != other_symbol and len(price_data[other_symbol]) >= 10:
                    other_returns = np.diff(price_data[other_symbol]) / price_data[other_symbol][:-1]
                    
                    # 计算相关系数
                    min_len = min(len(symbol_returns), len(other_returns))
                    corr = np.corrcoef(symbol_returns[-min_len:], other_returns[-min_len:])[0, 1]
                    
                    if not np.isnan(corr):
                        max_corr = max(max_corr, abs(corr))
            
            correlations[symbol] = max_corr
        
        return correlations

class AdvancedTradingSystem:
    """高级交易系统"""
    
    def __init__(self, initial_capital: float = 10000):
        self.technical_analyzer = AdvancedTechnicalAnalyzer()
        self.ml_analyzer = MachineLearningAnalyzer()
        self.risk_manager = AdvancedRiskManager(initial_capital)
        self.portfolio_manager = AdaptivePortfolioManager()
        self.positions = {}
        self.trades_history = []
        self.signal_history = []
        
    def generate_advanced_signals(self, symbol: str, df: pd.DataFrame) -> Optional[TradingSignal]:
        """生成高级交易信号"""
        if len(df) < 50:
            return None
        
        current_price = df['close'].iloc[-1]
        
        # 计算技术指标
        indicators = self.technical_analyzer.calculate_indicators(df)
        if not indicators:
            return None
        
        # 检测形态
        patterns = self.technical_analyzer.detect_patterns(df)
        
        # ML预测
        ml_prediction, ml_confidence = self.ml_analyzer.predict_signal(indicators)
        
        # 综合信号生成
        signal_strength = SignalStrength.WEAK
        signal_type = "hold"
        confidence = 0.5
        trade_type = TradeType.DAY
        risk_reward_ratio = 2.0
        expected_return = 0.0
        
        # 多维度信号确认
        buy_signals = 0
        sell_signals = 0
        
        # 技术指标确认
        if indicators.get('rsi', 50) < 30:  # 超卖
            buy_signals += 1
        elif indicators.get('rsi', 50) > 70:  # 超买
            sell_signals += 1
        
        # 均线系统
        sma_10 = indicators.get('sma_10', current_price)
        sma_20 = indicators.get('sma_20', current_price)
        sma_50 = indicators.get('sma_50', current_price)
        
        if sma_10 > sma_20 > sma_50:  # 多头排列
            buy_signals += 1
        elif sma_10 < sma_20 < sma_50:  # 空头排列
            sell_signals += 1
        
        # MACD确认
        macd = indicators.get('macd', 0)
        macd_signal = indicators.get('macd_signal', 0)
        
        if macd > macd_signal:
            buy_signals += 1
        else:
            sell_signals += 1
        
        # 布林带确认
        bb_upper = indicators.get('bb_upper', current_price * 1.05)
        bb_lower = indicators.get('bb_lower', current_price * 0.95)
        
        if current_price < bb_lower:  # 价格触及下轨
            buy_signals += 1
        elif current_price > bb_upper:  # 价格触及上轨
            sell_signals += 1
        
        # 随机指标确认
        stoch_k = indicators.get('stoch_k', 50)
        stoch_d = indicators.get('stoch_d', 50)
        
        if stoch_k < 20 and stoch_k > stoch_d:  # 超卖金叉
            buy_signals += 1
        elif stoch_k > 80 and stoch_k < stoch_d:  # 超买死叉
            sell_signals += 1
        
        # ADX趋势强度
        adx = indicators.get('adx', 25)
        if adx > 25:  # 趋势较强
            buy_signals += 0.5 if buy_signals > sell_signals else 0
            sell_signals += 0.5 if sell_signals > buy_signals else 0
        
        # ML预测
        if ml_prediction == 1:  # 预测上涨
            buy_signals += ml_confidence
        elif ml_prediction == -1:  # 预测下跌
            sell_signals += ml_confidence
        
        # 形态确认
        if "breakout" in patterns:
            buy_signals += 1
        if "double_bottom" in patterns:
            buy_signals += 1
        if "head_and_shoulders" in patterns:
            sell_signals += 1
        
        # 生成信号
        if buy_signals >= 4:  # 强买入信号
            signal_type = "buy"
            if buy_signals >= 5:
                signal_strength = SignalStrength.VERY_STRONG
            elif buy_signals >= 4:
                signal_strength = SignalStrength.STRONG
            confidence = min(1.0, buy_signals / 6.0)
            expected_return = 0.03  # 预期3%收益
        elif sell_signals >= 4:  # 强卖出信号
            signal_type = "sell"
            if sell_signals >= 5:
                signal_strength = SignalStrength.VERY_STRONG
            elif sell_signals >= 4:
                signal_strength = SignalStrength.STRONG
            confidence = min(1.0, sell_signals / 6.0)
            expected_return = -0.03  # 预期-3%收益
        elif buy_signals >= 3:  # 中等买入信号
            signal_type = "buy"
            signal_strength = SignalStrength.MODERATE
            confidence = min(1.0, buy_signals / 6.0)
            expected_return = 0.015  # 预期1.5%收益
        elif sell_signals >= 3:  # 中等卖出信号
            signal_type = "sell"
            signal_strength = SignalStrength.MODERATE
            confidence = min(1.0, sell_signals / 6.0)
            expected_return = -0.015  # 预期-1.5%收益
        
        if signal_type != "hold":
            # 确定交易类型
            if adx > 35:  # 强趋势
                trade_type = TradeType.POSITION
                risk_reward_ratio = 3.0
            elif adx > 25:  # 中等趋势
                trade_type = TradeType.SWING
                risk_reward_ratio = 2.5
            else:  # 横盘
                trade_type = TradeType.DAY
                risk_reward_ratio = 2.0
            
            # 计算入场价、止损和止盈
            volatility = indicators.get('stddev', 0.02)
            atr = indicators.get('atr', current_price * 0.02)
            
            entry_price = current_price
            stop_loss = self.risk_manager.calculate_stop_loss(
                entry_price, 
                PositionSide.LONG if signal_type == "buy" else PositionSide.SHORT,
                volatility, 
                atr
            )
            take_profit = self.risk_manager.calculate_take_profit(
                entry_price,
                PositionSide.LONG if signal_type == "buy" else PositionSide.SHORT,
                risk_reward_ratio,
                stop_loss
            )
            
            # 更新指标字典
            indicators['patterns'] = patterns
            indicators['ml_prediction'] = ml_prediction
            indicators['ml_confidence'] = ml_confidence
            
            return TradingSignal(
                symbol=symbol,
                signal_type=signal_type,
                strength=signal_strength,
                entry_price=entry_price,
                target_price=take_profit,
                stop_loss=stop_loss,
                confidence=confidence,
                timestamp=datetime.now(),
                indicators=indicators,
                trade_type=trade_type,
                risk_reward_ratio=risk_reward_ratio,
                expected_return=expected_return
            )
        
        return None
    
    def execute_trade(self, signal: TradingSignal) -> Optional[Position]:
        """执行交易"""
        # 检查风险管理
        if not self.risk_manager.should_trade(
            signal.entry_price, 
            signal.stop_loss, 
            PositionSide.LONG if signal.signal_type == "buy" else PositionSide.SHORT
        ):
            return None
        
        # 计算仓位大小
        volatility = signal.indicators.get('stddev', 0.02)
        position_size = self.risk_manager.calculate_position_size(
            signal.entry_price, 
            signal.stop_loss,
            signal.confidence,
            volatility
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
            timestamp=datetime.now(),
            stop_loss=signal.stop_loss,
            take_profit=signal.target_price
        )
        
        self.positions[signal.symbol] = position
        self.trades_history.append({
            'symbol': signal.symbol,
            'side': signal.signal_type,
            'size': position_size,
            'price': signal.entry_price,
            'timestamp': signal.timestamp,
            'confidence': signal.confidence,
            'strength': signal.strength.name,
            'trade_type': signal.trade_type.value
        })
        self.signal_history.append(signal)
        
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
    
    def should_close_position(self, position: Position, current_price: float) -> Tuple[bool, str]:
        """判断是否应该平仓"""
        reason = ""
        
        # 止损检查
        if position.side == PositionSide.LONG:
            if current_price <= position.stop_loss:
                return True, "stop_loss_triggered"
        else:
            if current_price >= position.stop_loss:
                return True, "stop_loss_triggered"
        
        # 止盈检查
        if position.side == PositionSide.LONG:
            if current_price >= position.take_profit:
                return True, "take_profit_reached"
        else:
            if current_price <= position.take_profit:
                return True, "take_profit_reached"
        
        # 时间平仓（根据交易类型）
        time_held = (datetime.now() - position.timestamp).total_seconds() / 3600  # 小时
        
        if position.side == TradeType.DAY.value and time_held > 6:  # 日内交易超过6小时
            return True, "time_exit_day_trade"
        elif position.side == TradeType.SCALP.value and time_held > 1:  # 抢帽子交易超过1小时
            return True, "time_exit_scalp_trade"
        
        return False, ""

def simulate_market_data(periods: int = 100) -> pd.DataFrame:
    """模拟市场数据"""
    np.random.seed(42)
    
    # 生成随机价格序列
    returns = np.random.normal(0.001, 0.02, periods)  # 日收益率，均值0.1%，标准差2%
    prices = [67000]  # 初始价格
    
    for ret in returns:
        new_price = prices[-1] * (1 + ret)
        prices.append(new_price)
    
    # 生成其他数据
    high = [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices]
    low = [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices]
    volume = [np.random.randint(1000, 5000) for _ in prices]
    
    df = pd.DataFrame({
        'close': prices,
        'high': high,
        'low': low,
        'open': [p * (1 + np.random.normal(0, 0.005)) for p in prices],
        'volume': volume
    })
    
    return df

def main():
    """主函数 - 演示高级AI交易系统"""
    print("🤖 启动先进AI交易决策系统")
    print("="*70)
    
    # 创建系统实例
    trading_system = AdvancedTradingSystem(initial_capital=10000)
    
    print("📊 准备模拟市场数据...")
    df = simulate_market_data(periods=200)
    print(f"📈 模拟数据: {len(df)} 个时间点")
    print(f"💰 初始资金: ${trading_system.risk_manager.initial_capital:,.2f}")
    
    # 生成交易信号
    print("\n🔍 生成高级交易信号...")
    signal = trading_system.generate_advanced_signals("BTC/USDT", df)
    
    if signal:
        print(f"🎯 生成交易信号: {signal.signal_type.upper()} {signal.symbol}")
        print(f"📊 信号强度: {signal.strength.name}")
        print(f"📈 入场价: ${signal.entry_price:,.2f}")
        print(f"🎯 止盈价: ${signal.target_price:,.2f}")
        print(f"🛑 止损价: ${signal.stop_loss:,.2f}")
        print(f"💯 置信度: {signal.confidence:.2f}")
        print(f"⚖️  风险回报比: {signal.risk_reward_ratio:.1f}")
        print(f"📊 交易类型: {signal.trade_type.value}")
        print(f"🎯 预期收益: {signal.expected_return*100:.2f}%")
        
        # 执行交易
        print("\n💼 执行交易...")
        position = trading_system.execute_trade(signal)
        if position:
            print(f"✅ 交易执行成功: {position.size:.6f} {position.symbol}")
            print(f"💰 仓位价值: ${position.size * position.entry_price:,.2f}")
            print(f"📊 止损价: ${position.stop_loss:.2f}")
            print(f"📊 止盈价: ${position.take_profit:.2f}")
        else:
            print("❌ 交易未执行（风险管理限制）")
    else:
        print("❌ 未生成有效交易信号")
        print("💡 系统将继续监控市场寻找机会")
    
    # 展示技术指标
    print("\n📊 高级技术指标分析:")
    indicators = trading_system.technical_analyzer.calculate_indicators(df)
    
    if indicators:
        print(f"   RSI: {indicators.get('rsi', 0):.2f}")
        print(f"   MACD: {indicators.get('macd', 0):.2f}")
        print(f"   SMA(20): ${indicators.get('sma_20', 0):,.2f}")
        print(f"   SMA(50): ${indicators.get('sma_50', 0):,.2f}")
        print(f"   ATR: {indicators.get('atr', 0):.2f}")
        print(f"   波动率: {indicators.get('stddev', 0):.4f}")
    
    # 展示形态检测
    patterns = trading_system.technical_analyzer.detect_patterns(df)
    if patterns:
        print(f"\n🔍 检测到技术形态: {', '.join(patterns)}")
    
    print("\n🎯 先进AI交易决策系统已深度优化!")
    print("💡 系统现在具备:")
    print("   • 多维度技术分析")
    print("   • 机器学习预测")
    print("   • 动态风险管理")
    print("   • 自适应投资组合管理")
    print("   • 智能信号生成")
    print("   • 形态识别能力")
    
    return trading_system

if __name__ == "__main__":
    system_instance = main()