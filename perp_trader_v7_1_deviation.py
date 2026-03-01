#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million Perpetual v7.1 - 趋势跟踪 + 差值分析版
使用 OKX 真实市场数据 + 差值图分析
"""
import ccxt
import time
import json
from datetime import datetime

class PerpetualTraderV7_1:
    def __init__(self):
        self.balance = 699.87
        self.initial_balance = 699.87
        self.leverage = 30
        # 账户风险 2% = 价格变动 2%/30 = 0.067%
        self.stop_loss_pct = 0.02 / self.leverage  # 2% 账户风险止损
        # 账户收益 8% = 价格变动 8%/30 = 0.267%
        self.take_profit_pct = 0.08 / self.leverage  # 8% 账户风险止盈
        self.position = None
        self.trades = []
        self.scan_count = 0
        self.session_start = datetime.now()
        
        # 初始化 OKX 测试网
        self.okx = ccxt.okx({
            'apiKey': '',
            'secret': '',
            'password': '',
            'enableRateLimit': True,
        })
        self.okx.set_sandbox_mode(True)  # 测试网
        
        # 交易对配置
        self.symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT']
        
    def get_ohlcv(self, symbol, timeframe='5m', limit=50):
        """获取K线数据"""
        try:
            ohlcv = self.okx.fetch_ohlcv(symbol, timeframe, limit=limit)
            return ohlcv
        except Exception as e:
            print(f"获取K线失败: {e}")
            return None
    
    def calculate_ma(self, ohlcv, period=20):
        """计算移动平均线"""
        if not ohlcv or len(ohlcv) < period:
            return None
        closes = [c[4] for c in ohlcv[-period:]]
        return sum(closes) / period
    
    def calculate_ma_deviation(self, ohlcv):
        """计算价格偏离MA的百分比"""
        ma20 = self.calculate_ma(ohlcv, 20)
        if not ma20:
            return 0
        current_price = ohlcv[-1][4]
        deviation = (current_price - ma20) / ma20 * 100
        return deviation
    
    def calculate_rsi(self, ohlcv, period=14):
        """计算RSI"""
        if not ohlcv or len(ohlcv) < period + 1:
            return 50
        closes = [c[4] for c in ohlcv]
        gains = []
        losses = []
        for i in range(1, len(closes)):
            change = closes[i] - closes[i-1]
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
    
    def calculate_bollinger_deviation(self, ohlcv, period=20):
        """计算布林带偏离"""
        if not ohlcv or len(ohlcv) < period:
            return 0
        closes = [c[4] for c in ohlcv[-period:]]
        ma = sum(closes) / period
        variance = sum((c - ma) ** 2 for c in closes) / period
        std = variance ** 0.5
        current_price = ohlcv[-1][4]
        deviation = (current_price - ma) / std if std > 0 else 0
        return deviation
    
    def calculate_volume_ratio(self, ohlcv, period=20):
        """计算成交量比率"""
        if not ohlcv or len(ohlcv) < period:
            return 1.0
        volumes = [c[5] for c in ohlcv[-period:]]
        avg_volume = sum(volumes) / period
        current_volume = ohlcv[-1][5]
        return current_volume / avg_volume if avg_volume > 0 else 1.0
    
    def calculate_momentum(self, ohlcv, period=10):
        """计算动量"""
        if not ohlcv or len(ohlcv) < period:
            return 0
        current = ohlcv[-1][4]
        past = ohlcv[-period][4]
        return (current - past) / past * 100
    
    def get_trend(self, ohlcv):
        """判断趋势"""
        ma20 = self.calculate_ma(ohlcv, 20)
        ma50 = self.calculate_ma(ohlcv, 50) if len(ohlcv) >= 50 else ma20
        current_price = ohlcv[-1][4]
        
        if ma20 and ma50:
            if current_price > ma20 > ma50:
                return 'UPTREND'
            elif current_price < ma20 < ma50:
                return 'DOWNTREND'
        return 'SIDEWAYS'
    
    def analyze_market(self, symbol):
        """综合市场分析"""
        ohlcv = self.get_ohlcv(symbol)
        if not ohlcv:
            return None
        
        current_price = ohlcv[-1][4]
        rsi = self.calculate_rsi(ohlcv)
        ma_deviation = self.calculate_ma_deviation(ohlcv)
        bb_deviation = self.calculate_bollinger_deviation(ohlcv)
        volume_ratio = self.calculate_volume_ratio(ohlcv)
        momentum = self.calculate_momentum(ohlcv)
        trend = self.get_trend(ohlcv)
        
        analysis = {
            'symbol': symbol,
            'price': current_price,
            'rsi': rsi,
            'ma_deviation': ma_deviation,
            'bb_deviation': bb_deviation,
            'volume_ratio': volume_ratio,
            'momentum': momentum,
            'trend': trend
        }
        
        return analysis
    
    def generate_signal(self, analysis):
        """基于差值分析生成信号"""
        if not analysis:
            return 'HOLD'
        
        rsi = analysis['rsi']
        ma_dev = analysis['ma_deviation']
        bb_dev = analysis['bb_deviation']
        volume = analysis['volume_ratio']
        momentum = analysis['momentum']
        trend = analysis['trend']
        
        score = 0
        
        # RSI 评分 (权重: 2)
        if rsi < 35:
            score += 3
        elif rsi < 45:
            score += 1
        elif rsi > 65:
            score -= 3
        elif rsi > 55:
            score -= 1
        
        # MA 偏离评分 (权重: 2)
        if ma_dev < -2:
            score += 2
        elif ma_dev < -1:
            score += 1
        elif ma_dev > 2:
            score -= 2
        elif ma_dev > 1:
            score -= 1
        
        # 布林带偏离 (权重: 1.5)
        if bb_dev < -2:
            score += 1.5
        elif bb_dev > 2:
            score -= 1.5
        
        # 成交量 (权重: 1)
        if volume > 1.5:
            if score > 0:
                score += 1
            elif score < 0:
                score -= 1
        elif volume < 0.5:
            score *= 0.8
        
        # 动量 (权重: 1)
        if momentum > 1:
            score += 1
        elif momentum < -1:
            score -= 1
        
        # 趋势确认
        if trend == 'UPTREND':
            score += 0.5
        elif trend == 'DOWNTREND':
            score -= 0.5
        
        if score >= 1.5:
            return 'LONG'
        elif score <= -1.5:
            return 'SHORT'
        
        return 'HOLD'
    
    def check_exit(self, symbol, entry_price, side):
        """检查出场信号"""
        try:
            ticker = self.okx.fetch_ticker(symbol)
            current_price = ticker['last']
        except:
            return False, 0
        
        if side == 'LONG':
            pnl_pct = (current_price - entry_price) / entry_price
        else:
            pnl_pct = (entry_price - current_price) / entry_price
        
        if pnl_pct >= self.take_profit_pct or pnl_pct <= -self.stop_loss_pct:
            return True, pnl_pct
        
        return False, pnl_pct
    
    def run(self):
        print("="*60)
        print("Web3Million v7.1 - 趋势跟踪 + 差值分析版")
        print("使用 OKX 真实市场数据 + 差值图分析")
        print("="*60)
        
        while True:
            self.scan_count += 1
            
            for symbol in self.symbols:
                if self.position is None:
                    analysis = self.analyze_market(symbol)
                    if analysis:
                        signal = self.generate_signal(analysis)
                        price = analysis['price']
                        
                        print(f"[{self.scan_count}] 分析 {symbol}: RSI={analysis['rsi']:.1f}, MA偏离={analysis['ma_deviation']:.2f}%, 动量={analysis['momentum']:.2f}%, 信号={signal}")
                        
                        if signal != 'HOLD':
                            self.position = {
                                'symbol': symbol,
                                'side': signal,
                                'entry_price': price,
                                'entry_time': datetime.now().isoformat()
                            }
                            emoji = '🟢' if signal == 'LONG' else '🔴'
                            print(f"[{self.scan_count}] {emoji} 开仓 {signal} {symbol} @ ${price:.2f}")
                else:
                    symbol = self.position['symbol']
                    side = self.position['side']
                    entry_price = self.position['entry_price']
                    
                    should_exit, pnl_pct = self.check_exit(symbol, entry_price, side)
                    
                    if should_exit:
                        # 带杠杆的实际盈亏
                        pnl = self.balance * pnl_pct * self.leverage
                        self.balance += pnl
                        emoji = '✅' if pnl > 0 else '❌'
                        print(f"[{self.scan_count}] {emoji} 平仓 {side} | 价格 PnL: {pnl_pct*100:.2f}% | 实际 PnL: {pnl_pct*self.leverage*100:.2f}% | 余额: ${self.balance:.2f}")
                        self.trades.append({
                            'symbol': symbol,
                            'side': side,
                            'entry': entry_price,
                            'pnl_pct': pnl_pct,
                            'time': datetime.now().isoformat()
                        })
                        self.position = None
            
            if self.position:
                symbol = self.position['symbol']
                side = self.position['side']
                entry = self.position['entry_price']
                
                try:
                    ticker = self.okx.fetch_ticker(symbol)
                    current = ticker['last']
                except:
                    current = entry
                
                if side == 'LONG':
                    pnl = (current - entry) / entry * 100
                else:
                    pnl = (entry - current) / entry * 100
                
                print(f"[{self.scan_count}] 持仓 {side} | PnL: {pnl:.2f}% | 余额: ${self.balance:.2f}")
            else:
                print(f"[{self.scan_count}] 等待信号...")
            
            time.sleep(30)

if __name__ == '__main__':
    try:
        trader = PerpetualTraderV7_1()
        trader.run()
    except KeyboardInterrupt:
        print("\n停止交易")
