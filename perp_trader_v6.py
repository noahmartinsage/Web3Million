#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million Perpetual v6 - Enhanced Trading System
Optimizations: Cooldown, Dynamic Position, RSI Tighter, Multi-TF, Volume Filter
"""
import ccxt
import pandas as pd
import time
import sys
import os
import json
from datetime import datetime

# Force unbuffered output
sys.stdout = sys.__stdout__
sys.stderr = sys.__stderr__

class PerpetualTraderV6:
    def __init__(self):
        self.exchange = ccxt.okx({
            'apiKey': 'b71ee824-5524-4cde-b818-b8e294c27d56',
            'secret': '76122A8879980469F474F042135584DB',
            'password': 'Qian159.',
            'testnet': True,
            'options': {'defaultType': 'swap'},
            'enableRateLimit': True,
            'timeout': 30000,
            'proxies': {
                'http': 'http://127.0.0.1:7890',
                'https': 'http://127.0.0.1:7890',
            }
        })
        
        self.symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT']
        
        # ============ OPTIMIZED PARAMS ============
        # Risk Management
        self.position_pct = 0.02  # 2% of balance (dynamic)
        self.max_position_usdt = 50  # Max $50 per trade
        self.min_position_eth = 0.01
        
        # Leverage
        self.leverage = 30  # Reduced from 50 for safety
        
        # Stop Loss / Take Profit
        self.stop_loss_pct = 0.02  # 2% (slightly wider)
        self.take_profit_pct = 0.06  # 6% (more realistic)
        
        # Cooldown (NEW)
        self.cooldown_seconds = 300  # 5 min between trades
        self.cooldown_after_loss = 600  # 10 min after loss
        self.last_trade_time = 0
        self.last_loss_time = 0
        
        # RSI thresholds (TIGHTER)
        self.rsi_oversold = 30  # was 35
        self.rsi_overbought = 70  # was 65
        
        # State
        self.position = None
        self.symbol = None
        self.entry_price = 0
        self.trades = []
        self.total_pnl = 0
        
        # Load state
        self.state_file = 'v6_state.json'
        self.load_state()
        
        print("="*60)
        print("Web3Million Perpetual v6 - Enhanced")
        print("="*60)
        
        print("Loading markets...")
        self.exchange.load_markets()
        print("Markets loaded!")
    
    def save_state(self):
        """Persist state to file"""
        state = {
            'position': self.position,
            'symbol': self.symbol,
            'entry_price': self.entry_price,
            'trades': self.trades[-100:],  # Keep last 100
            'total_pnl': self.total_pnl,
            'last_trade_time': self.last_trade_time,
            'last_loss_time': self.last_loss_time
        }
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f)
        except:
            pass
    
    def load_state(self):
        """Load state from file"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.position = state.get('position')
                    self.symbol = state.get('symbol')
                    self.entry_price = state.get('entry_price', 0)
                    self.trades = state.get('trades', [])
                    self.total_pnl = state.get('total_pnl', 0)
                    self.last_trade_time = state.get('last_trade_time', 0)
                    self.last_loss_time = state.get('last_loss_time', 0)
                print(f"State loaded: {len(self.trades)} trades, PnL: ${self.total_pnl:.2}")
            except:
                print("Failed to load state, starting fresh")
    
    def get_balance(self):
        try:
            bal = self.exchange.fetch_balance()
            return bal['total'].get('USDT', 0)
        except:
            return 0
    
    def get_ticker(self, symbol):
        try:
            return self.exchange.fetch_ticker(symbol)
        except:
            return None
    
    def set_leverage(self, symbol, leverage):
        try:
            self.exchange.set_leverage(leverage, symbol)
            return True
        except:
            return False
    
    def calculate_indicators(self, df):
        if df.empty or len(df) < 30:
            return df
        
        closes = df['c']
        volumes = df['v']
        
        # RSI
        delta = closes.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        df['rsi'] = 100 - (100 / (1 + gain / loss))
        
        # MACD
        ema12 = closes.ewm(span=12).mean()
        ema26 = closes.ewm(span=26).mean()
        df['macd'] = ema12 - ema26
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # MA
        df['ma5'] = closes.rolling(5).mean()
        df['ma20'] = closes.rolling(20).mean()
        df['ma50'] = closes.rolling(50).mean()  # NEW
        
        # Volume (NEW)
        df['volume_ma'] = volumes.rolling(20).mean()
        
        # Trend strength
        df['trend'] = 1 if df['ma5'].iloc[-1] > df['ma20'].iloc[-1] else -1
        
        return df
    
    def get_signal(self, symbol, timeframe='15m'):
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=60)
            df = pd.DataFrame(ohlcv, columns=['t','o','h','l','c','v'])
            df = self.calculate_indicators(df)
            
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            
            rsi = latest['rsi']
            macd_hist = latest['macd_hist']
            macd_hist_prev = prev['macd_hist']
            ma_trend = latest['trend']
            
            # Volume filter (NEW)
            volume_ratio = latest['v'] / latest['volume_ma'] if latest['volume_ma'] > 0 else 1
            
            # Tighter RSI thresholds
            if (rsi <= self.rsi_oversold and 
                macd_hist > macd_hist_prev and 
                ma_trend > 0 and
                volume_ratio > 0.8):  # Volume confirmation
                return 'LONG', latest['c'], rsi
            
            elif (rsi >= self.rsi_overbought and 
                  macd_hist < macd_hist_prev and 
                  ma_trend < 0 and
                  volume_ratio > 0.8):
                return 'SHORT', latest['c'], rsi
            
            return 'NEUTRAL', latest['c'], rsi
        except Exception as e:
            print(f"Signal error {symbol}: {e}")
            return 'NEUTRAL', 0, 50
    
    def check_higher_tf_trend(self, symbol):
        """Multi-timeframe confirmation (NEW)"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, '1h', limit=50)
            df = pd.DataFrame(ohlcv, columns=['t','o','h','l','c','v'])
            df['ma20'] = df['c'].rolling(20).mean()
            df['ma50'] = df['c'].rolling(50).mean()
            
            if df['ma20'].iloc[-1] > df['ma50'].iloc[-1]:
                return 1  # Uptrend
            elif df['ma20'].iloc[-1] < df['ma50'].iloc[-1]:
                return -1  # Downtrend
            return 0
        except:
            return 0  # Neutral if error
    
    def scan_opportunities(self):
        now = time.time()
        
        # Check cooldown
        if now - self.last_trade_time < self.cooldown_seconds:
            return None
        
        # Check cooldown after loss
        if now - self.last_loss_time < self.cooldown_after_loss:
            return None
        
        for symbol in self.symbols:
            # Check higher TF trend first
            hf_trend = self.check_higher_tf_trend(symbol)
            
            # Get signal
            signal, price, rsi = self.get_signal(symbol)
            
            if signal != 'NEUTRAL':
                # Confirm with higher timeframe
                if signal == 'LONG' and hf_trend >= 0:
                    continue
                if signal == 'SHORT' and hf_trend <= 0:
                    continue
                    
                return {'symbol': symbol, 'signal': signal, 'price': price, 'rsi': rsi}
        
        return None
    
    def calculate_position_size(self):
        """Dynamic position sizing (NEW)"""
        balance = self.get_balance()
        price = self.get_ticker(self.symbol)['last']
        
        # Use 2% of balance, but cap at max
        usdt = min(balance * self.position_pct, self.max_position_usdt)
        
        # Convert to units
        amount = usdt / price
        
        # Ensure min amount
        if amount < self.min_position_eth:
            amount = self.min_position_eth
            
        return amount
    
    def open_position(self, symbol, side, amount=None):
        try:
            self.set_leverage(symbol, self.leverage)
            
            # Dynamic position size
            if amount is None:
                self.symbol = symbol
                amount = self.calculate_position_size()
            
            if side == 'LONG':
                order = self.exchange.create_market_buy_order(symbol, amount)
            else:
                order = self.exchange.create_market_sell_order(symbol, amount)
            
            self.symbol = symbol
            self.position = side
            self.entry_price = self.get_ticker(symbol)['last']
            self.last_trade_time = time.time()
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [OPEN] {side} {symbol} {amount:.4f} @ ${self.entry_price}")
            
            self.save_state()
            return True
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Open error: {e}")
            return False
    
    def close_position(self, reason):
        if not self.position or not self.symbol:
            return
        
        try:
            positions = self.exchange.fetch_positions([self.symbol])
            pos_size = 0
            for p in positions:
                if p.get('size', 0) != 0:
                    pos_size = abs(float(p.get('size', 0)))
                    break
            
            if pos_size > 0:
                if self.position == 'LONG':
                    self.exchange.create_market_sell_order(self.symbol, pos_size)
                else:
                    self.exchange.create_market_buy_order(self.symbol, pos_size)
                
                current = self.get_ticker(self.symbol)['last']
                
                if self.position == 'LONG':
                    pnl = (current - self.entry_price) * pos_size
                else:
                    pnl = (self.entry_price - current) * pos_size
                
                # Track loss for extra cooldown
                if pnl < 0:
                    self.last_loss_time = time.time()
                
                self.total_pnl += pnl
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [CLOSE] {self.position} {reason} @ ${current}, PnL: ${pnl:.2f}")
                
                self.trades.append({
                    'symbol': self.symbol,
                    'side': self.position,
                    'entry': self.entry_price,
                    'exit': current,
                    'pnl': pnl,
                    'time': datetime.now().isoformat()
                })
            
            self.position = None
            self.symbol = None
            self.entry_price = 0
            
            self.save_state()
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Close error: {e}")
    
    def check_exit(self):
        if not self.position or not self.symbol:
            return False, None
        
        current = self.get_ticker(self.symbol)['last']
        
        if self.position == 'LONG':
            pnl_pct = (current - self.entry_price) / self.entry_price
        else:
            pnl_pct = (self.entry_price - current) / self.entry_price
        
        if pnl_pct <= -self.stop_loss_pct:
            return True, f"SL {pnl_pct*100:.1f}%"
        
        if pnl_pct >= self.take_profit_pct:
            return True, f"TP {pnl_pct*100:.1f}%"
        
        return False, None
    
    def run_forever(self, interval=30):
        print(f"\nStarting 24/7 trading... (interval: {interval}s)")
        print("Press Ctrl+C to stop\n")
        
        i = 0
        while True:
            try:
                i += 1
                usdt = self.get_balance()
                
                # Check exit
                if self.position:
                    should_exit, reason = self.check_exit()
                    if should_exit:
                        self.close_position(reason)
                
                # Open new position
                if not self.position:
                    opp = self.scan_opportunities()
                    if opp:
                        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] [Signal] {opp['signal']} {opp['symbol']} @ ${opp['price']} RSI:{opp['rsi']:.1f}")
                        self.open_position(opp['symbol'], opp['signal'])
                
                # Status
                status = f"[{i}] "
                if self.position:
                    current = self.get_ticker(self.symbol)['last']
                    if self.position == 'LONG':
                        pnl_pct = (current - self.entry_price) / self.entry_price * 100
                    else:
                        pnl_pct = (self.entry_price - current) / self.entry_price * 100
                    
                    # Show cooldown if active
                    cooldown = ""
                    if time.time() - self.last_loss_time < self.cooldown_after_loss:
                        remaining = int(self.cooldown_after_loss - (time.time() - self.last_loss_time))
                        cooldown = f" (CD:{remaining}s)"
                    
                    status += f"{self.position} {self.symbol.split('/')[0]} @ ${current:.0} ({pnl_pct:+.1f}%){cooldown}"
                else:
                    status += f"Idle | USDT: ${usdt:.2f}"
                
                print(status)
                time.sleep(interval)
                
            except KeyboardInterrupt:
                print("\n\nStopping...")
                break
            except Exception as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Error: {e}")
                time.sleep(10)
        
        self.print_report()
    
    def print_report(self):
        print("\n" + "="*60)
        print("FINAL REPORT - v6 Enhanced")
        print("="*60)
        print(f"Total PnL: ${self.total_pnl:.2f}")
        print(f"Total Trades: {len(self.trades)}")
        
        if self.trades:
            wins = [t for t in self.trades if t['pnl'] > 0]
            losses = [t for t in self.trades if t['pnl'] <= 0]
            win_rate = len(wins) / len(self.trades) * 100 if self.trades else 0
            print(f"Win Rate: {win_rate:.1f}% ({len(wins)}/{len(self.trades)})")
            
            if wins:
                avg_win = sum(t['pnl'] for t in wins) / len(wins)
                print(f"Avg Win: ${avg_win:.2f}")
            if losses:
                avg_loss = sum(t['pnl'] for t in losses) / len(losses)
                print(f"Avg Loss: ${avg_loss:.2f}")
        
        print("="*60)


if __name__ == "__main__":
    trader = PerpetualTraderV6()
    trader.run_forever(interval=30)
