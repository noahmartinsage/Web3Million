#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million Perpetual v8 - Binance Testnet Edition
使用币安测试网 API (2026-03-01 配置)
"""
import ccxt
import pandas as pd
import time
import sys
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

sys.stdout = sys.__stdout__
sys.stderr = sys.__stderr__

class BinanceTestnetTrader:
    def __init__(self):
        # 币安测试网配置
        self.exchange = ccxt.binanceusdm({
            'apiKey': os.getenv('BINANCE_TESTNET_API_KEY'),
            'secret': os.getenv('BINANCE_TESTNET_SECRET_KEY'),
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future',
            }
        })
        
        # 启用测试网
        self.exchange.set_sandbox_mode(True)
        
        self.symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT']
        
        # 风险管理参数 (v7.2 优化版)
        self.leverage = 20  # 20x 杠杆
        self.position_pct = 0.02  # 2% 仓位
        self.max_position_usdt = 30  # 最大 $30
        self.stop_loss_pct = 0.05 / self.leverage  # 5% 账户风险止损
        self.take_profit_pct = 0.15 / self.leverage  # 15% 账户风险止盈
        self.cooldown_seconds = 300  # 5 分钟冷却
        self.rsi_oversold = 32  # 收紧 RSI
        self.rsi_overbought = 68
        
        # 状态跟踪
        self.position = None
        self.symbol = None
        self.entry_price = 0
        self.trades = []
        self.total_pnl = 0
        self.last_trade_time = None
        self.balance = 1000  # 测试网初始余额
        self.session_start = datetime.now()
        
        print("=" * 60)
        print("Web3Million Perpetual v8 - Binance Testnet")
        print("=" * 60)
        print(f"启动时间：{self.session_start.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"杠杆：{self.leverage}x")
        print(f"止损：{self.stop_loss_pct*100/self.leverage:.2f}% (价格)")
        print(f"止盈：{self.take_profit_pct*100/self.leverage:.2f}% (价格)")
        print("=" * 60)
        
        print("连接币安测试网...")
        try:
            self.exchange.load_markets()
            print("[OK] 市场数据加载成功!")
            
            # 测试连接
            balance = self.exchange.fetch_balance()
            print(f"[OK] 账户连接成功!")
            print(f"   USDT 余额：{balance.get('USDT', {}).get('free', 'N/A')}")
        except Exception as e:
            print(f"[WARN] 连接测试：{e}")
    
    def fetch_ohlcv(self, symbol, timeframe='1h', limit=100):
        """获取 K 线数据"""
        try:
            return self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        except Exception as e:
            print(f"获取 K 线失败：{e}")
            return None
    
    def calculate_rsi(self, prices, period=14):
        """计算 RSI"""
        if len(prices) < period + 1:
            return 50
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def calculate_ma(self, prices, period):
        """计算移动平均"""
        if len(prices) < period:
            return None
        return sum(prices[-period:]) / period
    
    def check_signals(self, symbol):
        """检查交易信号"""
        try:
            ohlcv = self.fetch_ohlcv(symbol, timeframe='1h', limit=100)
            if not ohlcv:
                return 'ERROR', None
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            close_prices = df['close'].tolist()
            current_price = close_prices[-1]
            
            # 技术指标
            rsi = self.calculate_rsi(close_prices)
            ma5 = self.calculate_ma(close_prices, 5)
            ma20 = self.calculate_ma(close_prices, 20)
            
            print(f"\n{symbol}")
            print(f"  价格：${current_price:,.2f}")
            print(f"  RSI: {rsi:.2f}")
            print(f"  MA5: ${ma5:,.2f} | MA20: ${ma20:,.2f}")
            
            # 趋势判断
            trend = 'BULLISH' if ma5 > ma20 else 'BEARISH'
            print(f"  趋势：{trend}")
            
            # 交易信号
            long_signal = rsi < self.rsi_oversold and ma5 > ma20
            short_signal = rsi > self.rsi_overbought and ma5 < ma20
            
            if long_signal:
                print(f"  信号：LONG (RSI 超卖 + 多头趋势)")
                return 'LONG', current_price
            elif short_signal:
                print(f"  信号：SHORT (RSI 超买 + 空头趋势)")
                return 'SHORT', current_price
            else:
                print(f"  信号：HOLD")
                return 'HOLD', current_price
                
        except Exception as e:
            print(f"分析错误 {symbol}: {e}")
            return 'ERROR', None
    
    def execute_trade(self, symbol, side, price):
        """执行交易"""
        try:
            # 计算仓位
            position_size = min(self.balance * self.position_pct, self.max_position_usdt)
            
            print(f"\n[TRADE] 执行交易:")
            print(f"   品种：{symbol}")
            print(f"   方向：{side}")
            print(f"   价格：${price:,.2f}")
            print(f"   仓位：${position_size:.2f}")
            
            # 模拟交易 (实际部署时替换为真实 API 调用)
            self.position = {
                'symbol': symbol,
                'side': side,
                'entry_price': price,
                'size': position_size,
                'open_time': datetime.now()
            }
            self.symbol = symbol
            self.entry_price = price
            self.last_trade_time = datetime.now()
            
            print(f"[OK] 交易执行成功!")
            return True
            
        except Exception as e:
            print(f"[ERROR] 交易失败：{e}")
            return False
    
    def check_position(self, current_price):
        """检查持仓盈亏"""
        if not self.position:
            return
        
        entry = self.position['entry_price']
        side = self.position['side']
        
        # 计算盈亏
        if side == 'LONG':
            pnl_pct = (current_price - entry) / entry
        else:
            pnl_pct = (entry - current_price) / entry
        
        pnl_usdt = pnl_pct * self.position['size'] * self.leverage
        
        print(f"   持仓盈亏：{pnl_pct*100:.2f}% (${pnl_usdt:.2f})")
        
        # 检查止损止盈
        if pnl_pct <= -self.stop_loss_pct:
            print(f"   [STOP LOSS] 触发止损!")
            self.close_position(current_price)
        elif pnl_pct >= self.take_profit_pct:
            print(f"   [TAKE PROFIT] 触发止盈!")
            self.close_position(current_price)
    
    def close_position(self, current_price):
        """平仓"""
        if not self.position:
            return
        
        entry = self.position['entry_price']
        side = self.position['side']
        
        if side == 'LONG':
            pnl_pct = (current_price - entry) / entry
        else:
            pnl_pct = (entry - current_price) / entry
        
        pnl_usdt = pnl_pct * self.position['size'] * self.leverage
        self.balance += pnl_usdt
        self.total_pnl += pnl_usdt
        
        print(f"\n{'='*40}")
        print(f"平仓：{self.position['symbol']}")
        print(f"方向：{side} | 入场：${entry:,.2f} | 出场：${current_price:,.2f}")
        print(f"盈亏：${pnl_usdt:.2f} ({pnl_pct*100:.2f}%)")
        print(f"总盈亏：${self.total_pnl:.2f}")
        print(f"余额：${self.balance:.2f}")
        print(f"{'='*40}")
        
        self.position = None
        self.symbol = None
        self.entry_price = 0
    
    def run(self):
        """主循环"""
        print(f"\n[START] 开始 24/7 交易监控...")
        print(f"扫描间隔：30 秒")
        print(f"冷却时间：{self.cooldown_seconds}秒\n")
        
        scan_count = 0
        
        while True:
            try:
                scan_count += 1
                print(f"\n{'='*60}")
                print(f"[扫描 #{scan_count}] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"{'='*60}")
                
                # 扫描市场
                for symbol in self.symbols:
                    signal, price = self.check_signals(symbol)
                    
                    # 检查持仓
                    if self.position and self.position['symbol'] == symbol:
                        self.check_position(price)
                    
                    # 执行交易
                    if signal in ['LONG', 'SHORT'] and not self.position:
                        # 检查冷却
                        if self.last_trade_time:
                            cooldown_elapsed = (datetime.now() - self.last_trade_time).total_seconds()
                            if cooldown_elapsed < self.cooldown_seconds:
                                print(f"   冷却中... ({int(self.cooldown_seconds - cooldown_elapsed)}秒)")
                                continue
                        
                        self.execute_trade(symbol, signal, price)
                    
                    time.sleep(1)  # 速率限制
                
                print(f"\n[BALANCE] 当前余额：${self.balance:.2f}")
                print(f"[PNL] 总盈亏：${self.total_pnl:.2f}")
                
                # 等待下次扫描
                print(f"\n[WAIT] 30 秒后下次扫描...")
                time.sleep(30)
                
            except KeyboardInterrupt:
                print(f"\n\n[STOP] 手动停止")
                break
            except Exception as e:
                print(f"\n[ERROR] 错误：{e}")
                time.sleep(10)
        
        # 最终报告
        print(f"\n{'='*60}")
        print(f"交易会话总结")
        print(f"{'='*60}")
        print(f"运行时间：{datetime.now() - self.session_start}")
        print(f"总交易数：{len(self.trades)}")
        print(f"总盈亏：${self.total_pnl:.2f}")
        print(f"最终余额：${self.balance:.2f}")
        print(f"{'='*60}")

if __name__ == '__main__':
    trader = BinanceTestnetTrader()
    trader.run()
