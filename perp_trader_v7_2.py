#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million Perpetual v7.2 - 修复版
使用 OKX 测试网
修复问题：
1. 止损太紧 → 放宽到 5% 账户风险
2. 信号太敏感 → 提高阈值到 3.0
3. 趋势过滤 → 只顺趋势交易
4. 添加跟踪止盈
"""
import os
# 清除代理设置
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)

import ccxt
import time
import json
from datetime import datetime

class PerpetualTraderV7_2:
    def __init__(self):
        self.balance = 699.87
        self.initial_balance = 699.87
        self.leverage = 20  # 降低杠杆到 20x
        # 账户风险 5% = 价格变动 5%/20 = 0.25%
        self.stop_loss_pct = 0.05 / self.leverage  # 5% 账户风险止损
        # 账户收益 15% = 价格变动 15%/20 = 0.75%
        self.take_profit_pct = 0.15 / self.leverage  # 15% 账户风险止盈
        self.position = None
        self.trades = []
        self.scan_count = 0
        self.session_start = datetime.now()
        self.highest_price = 0
        self.lowest_price = float('inf')
        
        # 初始化 OKX 测试网 - 使用 IP 直连绕过代理
        self.okx = ccxt.okx({
            'apiKey': '',
            'secret': '',
            'password': '',
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'},
        })
        self.okx.set_sandbox_mode(True)  # 测试网
        
        # 禁用代理
        self.okx.session.trust_env = False
        self.okx.session.proxies = {}
        self.okx.session.verify = False
        
        # 修改 URL 使用 IP 直连
        import re
        for key in self.okx.urls:
            if isinstance(self.okx.urls[key], dict):
                for subkey in self.okx.urls[key]:
                    if isinstance(self.okx.urls[key][subkey], str):
                        self.okx.urls[key][subkey] = self.okx.urls[key][subkey].replace('www.okx.com', '43.199.3.187')
            elif isinstance(self.okx.urls[key], str):
                self.okx.urls[key] = self.okx.urls[key].replace('www.okx.com', '43.199.3.187')
        
        # 添加 Host header
        self.okx.headers['Host'] = 'www.okx.com'
        
        # 交易对配置
        self.symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT']
        
    def get_ohlcv(self, symbol, timeframe='15m', limit=50):
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
    
    def calculate_momentum(self, ohlcv, period=10):
        """计算动量"""
        if not ohlcv or len(ohlcv) < period:
            return 0
        current = ohlcv[-1][4]
        past = ohlcv[-period][4]
        return (current - past) / past * 100
    
    def get_trend(self, ohlcv):
        """判断趋势 - 使用更长的周期"""
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
        volume_ratio = self.calculate_volume_ratio(ohlcv)
        momentum = self.calculate_momentum(ohlcv)
        trend = self.get_trend(ohlcv)
        
        analysis = {
            'symbol': symbol,
            'price': current_price,
            'rsi': rsi,
            'ma_deviation': ma_deviation,
            'volume_ratio': volume_ratio,
            'momentum': momentum,
            'trend': trend
        }
        
        return analysis
    
    def calculate_volume_ratio(self, ohlcv, period=20):
        """计算成交量比率"""
        if not ohlcv or len(ohlcv) < period:
            return 1.0
        volumes = [c[5] for c in ohlcv[-period:]]
        avg_volume = sum(volumes) / period
        current_volume = ohlcv[-1][5]
        return current_volume / avg_volume if avg_volume > 0 else 1.0
    
    def generate_signal(self, analysis):
        """基于趋势过滤的信号生成 - 更严格的策略"""
        if not analysis:
            return 'HOLD'
        
        rsi = analysis['rsi']
        ma_dev = analysis['ma_deviation']
        momentum = analysis['momentum']
        trend = analysis['trend']
        volume = analysis['volume_ratio']
        
        score = 0
        
        # 趋势过滤 - 关键！
        if trend == 'SIDEWAYS':
            return 'HOLD'
        
        # RSI 评分 - 更严格
        if trend == 'UPTREND':
            if rsi < 30:
                score += 3  # 超卖做多
            elif rsi < 40:
                score += 1
            elif rsi > 70:
                score -= 2
        elif trend == 'DOWNTREND':
            if rsi > 70:
                score += 3  # 超买做空
            elif rsi > 60:
                score += 1
            elif rsi < 30:
                score -= 2
        
        # MA 偏离 - 顺趋势
        if trend == 'UPTREND':
            if ma_dev < -2:
                score += 2  # 回调到均线附近
            elif ma_dev < -1:
                score += 1
            elif ma_dev > 3:
                score -= 1  # 偏离太多
        elif trend == 'DOWNTREND':
            if ma_dev > 2:
                score += 2
            elif ma_dev > 1:
                score += 1
            elif ma_dev < -3:
                score -= 1
        
        # 动量确认
        if trend == 'UPTREND' and momentum > 0.5:
            score += 1
        elif trend == 'DOWNTREND' and momentum < -0.5:
            score += 1
        elif trend == 'UPTREND' and momentum < -1:
            score -= 1
        elif trend == 'DOWNTREND' and momentum > 1:
            score -= 1
        
        # 成交量确认
        if volume > 1.3 and score > 0:
            score += 0.5
        elif volume < 0.7:
            score -= 0.5
        
        # 提高阈值到 3.0
        if score >= 3.0:
            return 'LONG'
        elif score <= -3.0:
            return 'SHORT'
        
        return 'HOLD'
    
    def check_exit(self, symbol, entry_price, side):
        """检查出场信号 - 带跟踪止盈"""
        try:
            ticker = self.okx.fetch_ticker(symbol)
            current_price = ticker['last']
        except:
            return False, 0, current_price if 'current_price' in dir() else entry_price
        
        if side == 'LONG':
            pnl_pct = (current_price - entry_price) / entry_price
            # 更新最高价
            if current_price > self.highest_price:
                self.highest_price = current_price
            # 跟踪止盈：当价格回落 0.3% 时出场
            if self.highest_price > 0:
                retracement = (self.highest_price - current_price) / self.highest_price
                if retracement >= 0.003 and pnl_pct > 0.02:  # 回落 0.3% 且盈利 > 2%
                    return True, pnl_pct
        else:
            pnl_pct = (entry_price - current_price) / entry_price
            # 更新最低价
            if current_price < self.lowest_price:
                self.lowest_price = current_price
            # 跟踪止盈
            if self.lowest_price < float('inf'):
                retracement = (current_price - self.lowest_price) / self.lowest_price
                if retracement >= 0.003 and pnl_pct > 0.02:
                    return True, pnl_pct
        
        # 止损或止盈
        if pnl_pct >= self.take_profit_pct:
            return True, pnl_pct
        if pnl_pct <= -self.stop_loss_pct:
            return True, pnl_pct
        
        return False, pnl_pct
    
    def run(self):
        print("="*60)
        print("Web3Million v7.2 - 修复版")
        print("使用 OKX 测试网")
        print("改进：止损 5%、趋势过滤、跟踪止盈")
        print("="*60)
        
        while True:
            self.scan_count += 1
            
            for symbol in self.symbols:
                if self.position is None:
                    # 重置跟踪价格
                    self.highest_price = 0
                    self.lowest_price = float('inf')
                    
                    analysis = self.analyze_market(symbol)
                    if analysis:
                        signal = self.generate_signal(analysis)
                        price = analysis['price']
                        
                        print(f"[{self.scan_count}] 分析 {symbol}: RSI={analysis['rsi']:.1f}, MA偏离={analysis['ma_deviation']:.2f}%, 趋势={analysis['trend']}, 信号={signal}")
                        
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
        trader = PerpetualTraderV7_2()
        trader.run()
    except KeyboardInterrupt:
        print("\n停止交易")
