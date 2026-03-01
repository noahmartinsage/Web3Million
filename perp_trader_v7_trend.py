#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million Perpetual v7 - 趋势跟踪版 (真实数据)
使用 OKX 真实市场数据 + 趋势过滤
"""
import ccxt
import time
import json
from datetime import datetime

class PerpetualTraderV7:
    def __init__(self):
        self.balance = 1288.38
        self.initial_balance = 1288.38
        self.leverage = 30
        self.stop_loss_pct = 0.015  # 1.5% 止损
        self.take_profit_pct = 0.05  # 5% 止盈
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
        
    def get_ohlcv(self, symbol, timeframe='5m', limit=20):
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
    
    def get_trend(self, ohlcv):
        """判断趋势：简单基于 MA 和价格关系"""
        ma20 = self.calculate_ma(ohlcv, 20)
        ma50 = self.calculate_ma(ohlcv, 50) if len(ohlcv) >= 50 else ma20
        current_price = ohlcv[-1][4]
        
        if ma20 and ma50:
            if current_price > ma20 > ma50:
                return 'UPTREND'
            elif current_price < ma20 < ma50:
                return 'DOWNTREND'
        return 'SIDEWAYS'
    
    def check_entry(self, symbol):
        """检查入场信号"""
        ohlcv = self.get_ohlcv(symbol)
        if not ohlcv:
            return 'HOLD', None
        
        current_price = ohlcv[-1][4]
        rsi = self.calculate_rsi(ohlcv)
        trend = self.get_trend(ohlcv)
        
        # 多单信号: RSI低于40 + 上升趋势 或 突破
        if rsi < 40 and trend in ['UPTREND', 'SIDEWAYS']:
            return 'LONG', current_price
        
        # 空单信号: RSI高于60 + 下降趋势
        if rsi > 60 and trend in ['DOWNTREND', 'SIDEWAYS']:
            return 'SHORT', current_price
        
        return 'HOLD', current_price
    
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
        
        # 止盈或止损
        if pnl_pct >= self.take_profit_pct or pnl_pct <= -self.stop_loss_pct:
            return True, pnl_pct
        
        return False, pnl_pct
    
    def run(self):
        print("="*60)
        print("Web3Million Perpetual v7 - 趋势跟踪版")
        print("使用 OKX 真实市场数据")
        print("="*60)
        
        while True:
            self.scan_count += 1
            
            for symbol in self.symbols:
                if self.position is None:
                    # 无持仓，检查入场
                    signal, price = self.check_entry(symbol)
                    if signal != 'HOLD':
                        self.position = {
                            'symbol': symbol,
                            'side': signal,
                            'entry_price': price,
                            'entry_time': datetime.now().isoformat()
                        }
                        print(f"[{self.scan_count}] 🚀 OPEN {signal} {symbol} @ ${price:.2f}")
                else:
                    # 有持仓，检查出场
                    symbol = self.position['symbol']
                    side = self.position['side']
                    entry_price = self.position['entry_price']
                    
                    should_exit, pnl_pct = self.check_exit(symbol, entry_price, side)
                    
                    if should_exit:
                        pnl = self.balance * pnl_pct * self.leverage
                        self.balance += pnl
                        print(f"[{self.scan_count}] {'✅' if pnl > 0 else '❌'} CLOSE {side} | PnL: {pnl_pct*100:.2f}% | Balance: ${self.balance:.2f}")
                        self.trades.append({
                            'symbol': symbol,
                            'side': side,
                            'entry': entry_price,
                            'pnl_pct': pnl_pct,
                            'time': datetime.now().isoformat()
                        })
                        self.position = None
            
            # 输出状态
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
                
                print(f"[{self.scan_count}] 👤 HOLD {side} {symbol} | PnL: {pnl:.2f}% | Balance: ${self.balance:.2f}")
            else:
                print(f"[{self.scan_count}] 😴 Waiting for signal...")
            
            time.sleep(30)  # 30秒扫描一次

if __name__ == '__main__':
    try:
        trader = PerpetualTraderV7()
        trader.run()
    except KeyboardInterrupt:
        print("\n停止交易")
